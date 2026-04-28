#!/usr/bin/env python3
"""
Git operations script — single entry point for all git commands.
Usage:
    python scripts/git_ops.py status
    python scripts/git_ops.py add <file>...           # stage specific files only
    python scripts/git_ops.py commit "message"        # add . + commit (sweeps all changes)
    python scripts/git_ops.py commit_only "message"   # commit already-staged work only
    python scripts/git_ops.py push                    # auto-sets upstream on first push
    python scripts/git_ops.py pull
    python scripts/git_ops.py log
    python scripts/git_ops.py branch <name>
    python scripts/git_ops.py checkout <branch>
    python scripts/git_ops.py diff
    python scripts/git_ops.py remote_add <name> <url>
    python scripts/git_ops.py remotes                 # list configured remotes
"""

import subprocess
import sys


def run(cmd: list[str]) -> None:
    """Run a git command and print output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)


def status() -> None:
    """Show git status."""
    run(["git", "status", "--short"])


def commit(message: str) -> None:
    """Stage all and commit with message."""
    run(["git", "add", "."])
    run(["git", "commit", "-m", message])


def add(*files: str) -> None:
    """Stage specific files only."""
    if not files:
        print("Error: 'add' requires at least one file path")
        sys.exit(1)
    run(["git", "add", *files])


def commit_only(message: str) -> None:
    """Commit already-staged changes (no implicit add)."""
    run(["git", "commit", "-m", message])


def push() -> None:
    """Push to current branch; set upstream automatically on first push."""
    branch_proc = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    branch_name = branch_proc.stdout.strip()
    if not branch_name:
        print("Error: detached HEAD — not on any branch")
        sys.exit(1)

    upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        capture_output=True,
        text=True,
    )
    if upstream.returncode != 0:
        remotes = subprocess.run(
            ["git", "remote"], capture_output=True, text=True
        ).stdout.split()
        if "origin" not in remotes:
            print(
                "Error: no upstream set and no 'origin' remote configured. "
                "Run: python3 scripts/git_ops.py remote_add origin <url>"
            )
            sys.exit(1)
        run(["git", "push", "-u", "origin", branch_name])
        return

    run(["git", "push"])


def remote_add(name: str, url: str) -> None:
    """Add a new remote."""
    run(["git", "remote", "add", name, url])


def remotes() -> None:
    """List configured remotes."""
    run(["git", "remote", "-v"])


def pull() -> None:
    """Pull latest from current branch."""
    run(["git", "pull"])


def log() -> None:
    """Show last 10 commits."""
    run(["git", "log", "--oneline", "-n", "10"])


def branch(name: str) -> None:
    """Create and switch to a new branch."""
    run(["git", "checkout", "-b", name])


def checkout(name: str) -> None:
    """Switch to an existing branch."""
    run(["git", "checkout", name])


def diff() -> None:
    """Show unstaged changes."""
    run(["git", "diff", "--stat"])


COMMANDS = {
    "status": (status, 0, False),
    "add": (add, 1, True),
    "commit": (commit, 1, False),
    "commit_only": (commit_only, 1, False),
    "push": (push, 0, False),
    "pull": (pull, 0, False),
    "log": (log, 0, False),
    "branch": (branch, 1, False),
    "checkout": (checkout, 1, False),
    "diff": (diff, 0, False),
    "remote_add": (remote_add, 2, False),
    "remotes": (remotes, 0, False),
}


def main() -> None:
    """Parse command and execute."""
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: python scripts/git_ops.py <command> [args]")
        print(f"Commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    cmd_name = sys.argv[1]
    func, expected_args, variadic = COMMANDS[cmd_name]

    args = sys.argv[2:]
    if len(args) < expected_args:
        print(f"Error: '{cmd_name}' requires at least {expected_args} argument(s)")
        sys.exit(1)

    if variadic:
        func(*args)
    else:
        func(*args[:expected_args])


if __name__ == "__main__":
    main()
