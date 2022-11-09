#!/usr/bin/python -Bu

import argparse
import os
import pathlib
import subprocess
import sys

def banner(msg):
    print("")
    print(f"=" * (len(msg) + 6))
    print(f"=  {msg}  =")
    print(f"=" * (len(msg) + 6))

def section(msg):
    print(f"* {msg}")

#
# Helpers to interact with GitHub using the secure PAT token
# NOTE: Make sure anything logged do not print the environment which may contain the PAT
#
def getCommits(pr):
    """Generate a list of all commits in the PR"""
    cmd = os.path.join(pathlib.Path(__file__).parent.absolute(), "github/commits")
    result = subprocess.run([cmd, pr], capture_output=True, text=True, check=True)
    return list(filter(None, result.stdout.split("\n")))

def setState(runid, context, commit, state, description):
    """Helper to set state of each commit as it progress"""
    section(f"Set {state} status for {commit} in {context} context - {description}")

    cmd = os.path.join(pathlib.Path(__file__).parent.absolute(), "github/status")
    cmdline = [cmd, f"--context={context}", f"--description={description}", commit, state]
    if runid:
        cmdline.append(f"--runid={runid}")
    subprocess.run(cmdline, check=True)

def setStateAll(runid, commits, state, description):
    """Helper to set state of all commits, usefull for init and error out"""
    setState(runid, "dts", commits[-1], state, description)
    for commit in commits:
        setState(runid, "build", commit, state, description)

def clone(location):
    """Helper to clone the code using PAT, while also keeping the PAT secret"""
    cmd = os.path.join(pathlib.Path(__file__).parent.absolute(), "github/clone")
    return subprocess.run([cmd, location], text=True).returncode == 0

#
# = Wrappers for calling check scripts
# NOTE: Return True/False on Pass/Fail
#
def build(location, commit, baseline=False):
    section(f"Building {commit}")
    cmd = os.path.join(pathlib.Path(__file__).parent.absolute(), "check-build.sh")
    return subprocess.run([cmd, location, commit, "yes" if baseline else "no"], text=True).returncode == 0

def static(location, commit):
    section(f"Running static checks on {commit}")
    cmd = os.path.join(pathlib.Path(__file__).parent.absolute(), "check-static.sh")
    return subprocess.run([cmd, location], text=True).returncode == 0

def runtime(location, commit):
    section(f"Running runtime checks on {commit}")
    cmd = os.path.join(pathlib.Path(__file__).parent.absolute(), "check-runtime.sh")
    return subprocess.run([cmd, location], text=True).returncode == 0

def main():
    dpdk = os.path.join(pathlib.Path(__file__).parent.absolute(), "dpdk")
    parser = argparse.ArgumentParser(description='Entry point for test of PR')
    parser.add_argument("pr")
    parser.add_argument("--runid")
    args = parser.parse_args()

    banner("Mark all commits in PR as pending, to show work have started")
    commits = getCommits(args.pr)
    top = commits[-1]
    setStateAll(args.runid, commits, "pending", "Waiting")

    banner("Setup test execution environment and build baseline")
    # TODO: Add check that all tools and permissons are OK for runtime checks
    # TODO: Setup build enviorment (CCACHE)
    if not clone(dpdk) or not build(dpdk, f"{commits[0]}~1", True):
        setStateAll(args.runid, commits, "error", "Can not clone or build baseline")
        return 1

    banner("Compile and run static checks for each commit in PR")
    badcommit = False
    for commit in commits:
        if not build(dpdk, commit) or not static(dpdk, commit):
            setState(args.runid, "build", commit, "failure", "Commit failed to build or static checks")
            badcommit = True
            continue

        setState(args.runid, "build", commit, "success", "Passed build and static checks")

    banner(f"Run runtime checks on top-commit {top}")
    if badcommit:
        setState(args.runid, "dts", top, "error", "One or more commits failed build or static checks, will not proceed with runtime checks")
        return 1

    if not runtime(dpdk, top):
        setState(args.runid, "dts", top, "failure", "PR failed runtime checks")
        return 1

    setState(args.runid, "dts", top, "success", "Passed runtime checks")

    return 0

if __name__ == '__main__':
    sys.exit(main())
