"""Stage all operation."""

from typing import Optional

from git import Repo, GitCommandError


def stage_all(repo: Optional[Repo]) -> bool:
    """Stage all changes.

    Args:
        repo: Git repository object

    Returns:
        True if successful, False otherwise
    """
    if not repo:
        return False
    try:
        repo.git.add('-A')
        return True
    except GitCommandError:
        return False
