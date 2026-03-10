import subprocess
import os

def _run_git(command: list) -> str:
    """Helper to run git commands."""
    try:
        AGENT_ROOT = os.path.realpath(os.getenv("AGENT_ROOT", os.getcwd()))
        result = subprocess.run(
            ["git"] + command,
            cwd=AGENT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\nSTDERR: {result.stderr.strip()}"
        return f"Exit Code: {result.returncode}\n{output}"
    except Exception as e:
        return f"Error executing git command: {e}"

def git_status() -> str:
    """Returns the current git status."""
    return _run_git(["status"])

def git_checkout(branch: str, create_new: bool = False) -> str:
    """Checks out a git branch.

    Args:
        branch: The name of the branch to checkout.
        create_new: Whether to create a new branch with -b.
    """
    if create_new:
        return _run_git(["checkout", "-b", branch])
    return _run_git(["checkout", branch])

def git_commit(message: str, add_all: bool = True) -> str:
    """Commits changes to git.

    Args:
        message: The commit message.
        add_all: Whether to run 'git add .' before committing.
    """
    if add_all:
        add_res = _run_git(["add", "."])
        if "Exit Code: 0" not in add_res:
            return f"Failed to add files:\n{add_res}"
    return _run_git(["commit", "-m", message])

def git_push(branch: str = "HEAD") -> str:
    """Pushes the given branch to origin.

    Args:
        branch: The branch to push (defaults to current HEAD).
    """
    return _run_git(["push", "origin", branch])

def git_pull(branch: str = "main") -> str:
    """Pulls the latest changes from origin.

    Args:
        branch: The branch to pull (defaults to main).
    """
    return _run_git(["pull", "origin", branch])
