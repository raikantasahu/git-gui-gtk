"""Delete remote operation."""

from typing import Optional

from git import Repo, GitCommandError


def delete_remote(repo: Optional[Repo], name: str) -> tuple[bool, str]:
    """Delete a remote.

    Args:
        repo: Git repository object
        name: Remote name to delete

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.remote('remove', name)
        return True, f'Remote {name} deleted'
    except GitCommandError as e:
        return False, str(e)
