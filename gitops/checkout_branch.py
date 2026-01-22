"""Checkout branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def checkout_branch(repo: Optional[Repo], name: str) -> tuple[bool, str]:
    """Checkout a branch.

    Args:
        repo: Git repository object
        name: Branch name to checkout

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.checkout(name)
        return True, f'Switched to branch {name}'
    except GitCommandError as e:
        return False, str(e)
