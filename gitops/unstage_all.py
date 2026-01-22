"""Unstage all operation."""

from typing import Optional

from git import Repo, GitCommandError


def unstage_all(repo: Optional[Repo]) -> bool:
    """Unstage all changes.

    Args:
        repo: Git repository object

    Returns:
        True if successful, False otherwise
    """
    if not repo:
        return False
    try:
        repo.git.reset('HEAD')
        return True
    except GitCommandError:
        return False
