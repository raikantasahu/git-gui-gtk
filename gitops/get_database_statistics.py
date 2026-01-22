"""Get database statistics operation."""

from typing import Optional

from git import Repo, GitCommandError


def get_database_statistics(repo: Optional[Repo]) -> tuple[bool, str]:
    """Get git database statistics.

    Args:
        repo: Git repository object

    Returns:
        Tuple of (success, output/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        output = repo.git.count_objects('-v')
        return True, output
    except GitCommandError as e:
        return False, str(e)
