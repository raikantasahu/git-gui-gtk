"""Rename branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def rename_branch(repo: Optional[Repo], old_name: str, new_name: str) -> tuple[bool, str]:
    """Rename a branch.

    Args:
        repo: Git repository object
        old_name: Current branch name
        new_name: New branch name

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.branch('-m', old_name, new_name)
        return True, f'Branch {old_name} renamed to {new_name}'
    except GitCommandError as e:
        return False, str(e)
