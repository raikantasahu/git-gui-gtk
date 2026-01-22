"""Compress database operation."""

from typing import Optional

from git import Repo, GitCommandError


def compress_database(repo: Optional[Repo]) -> tuple[bool, str]:
    """Compress git database (git gc).

    Args:
        repo: Git repository object

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.gc()
        return True, 'Database compressed successfully'
    except GitCommandError as e:
        return False, str(e)
