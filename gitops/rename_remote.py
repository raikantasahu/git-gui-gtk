"""Rename remote operation."""

from typing import Optional

from git import Repo, GitCommandError


def rename_remote(repo: Optional[Repo], old_name: str, new_name: str) -> tuple[bool, str]:
    """Rename a remote.

    Args:
        repo: Git repository object
        old_name: Current remote name
        new_name: New remote name

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.remote('rename', old_name, new_name)
        return True, f'Remote {old_name} renamed to {new_name}'
    except GitCommandError as e:
        return False, str(e)
