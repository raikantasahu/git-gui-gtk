"""Stage file operation."""

from typing import Optional

from git import Repo


def stage_file(repo: Optional[Repo], path: str) -> bool:
    """Stage a file for commit.

    Args:
        repo: Git repository object
        path: File path to stage

    Returns:
        True if successful, False otherwise
    """
    if not repo:
        return False
    try:
        repo.index.add([path])
        return True
    except Exception:
        return False
