"""Revert file operation."""

from typing import Optional

from git import Repo, GitCommandError


def revert_file(repo: Optional[Repo], path: str) -> tuple[bool, str]:
    """Revert a file to its state in HEAD.

    Args:
        repo: Git repository object
        path: File path to revert

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'

    try:
        repo.git.checkout('HEAD', '--', path)
        return True, f'Reverted {path}'
    except GitCommandError as e:
        return False, str(e)
