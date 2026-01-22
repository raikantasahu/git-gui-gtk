"""Fetch operation."""

from typing import Optional, Callable

from git import Repo, GitCommandError


def fetch(repo: Optional[Repo], remote_name: str,
          progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
    """Fetch from remote.

    Args:
        repo: Git repository object
        remote_name: Name of the remote to fetch from
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'

    try:
        remote = repo.remote(remote_name)
        remote.fetch()
        return True, f'Fetch from {remote_name} successful'
    except GitCommandError as e:
        return False, str(e)
    except ValueError as e:
        return False, f'Remote not found: {e}'
