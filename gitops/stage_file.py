"""Stage file operation."""

from typing import Optional

from git import Repo

from gitops.models import FileStatus


def stage_file(repo: Optional[Repo], path: str, status: Optional[FileStatus] = None) -> bool:
    """Stage a file for commit.

    Args:
        repo: Git repository object
        path: File path to stage
        status: File status (used to handle deleted files via index.remove)

    Returns:
        True if successful, False otherwise
    """
    if not repo:
        return False
    try:
        if status == FileStatus.DELETED:
            repo.index.remove([path], working_tree=False)
        else:
            repo.index.add([path])
        return True
    except Exception:
        return False
