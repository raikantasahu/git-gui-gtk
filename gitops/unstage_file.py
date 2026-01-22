"""Unstage file operation."""

from typing import Optional

from git import Repo, GitCommandError


def unstage_file(repo: Optional[Repo], path: str) -> bool:
    """Unstage a file.

    Args:
        repo: Git repository object
        path: File path to unstage

    Returns:
        True if successful, False otherwise
    """
    if not repo:
        return False
    try:
        # Reset file in index to HEAD state
        repo.git.reset('HEAD', '--', path)
        return True
    except GitCommandError:
        # Might be a new file, try removing from index
        try:
            repo.index.remove([path], working_tree=False)
            return True
        except Exception:
            return False
