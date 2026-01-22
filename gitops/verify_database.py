"""Verify database operation."""

from typing import Optional

from git import Repo, GitCommandError


def verify_database(repo: Optional[Repo]) -> tuple[bool, str]:
    """Verify git database (git fsck).

    Args:
        repo: Git repository object

    Returns:
        Tuple of (success, output/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        output = repo.git.fsck()
        return True, output
    except GitCommandError as e:
        return False, str(e)
