"""Add remote operation."""

from typing import Optional

from git import Repo, GitCommandError


def add_remote(repo: Optional[Repo], name: str, url: str) -> tuple[bool, str]:
    """Add a new remote.

    Args:
        repo: Git repository object
        name: Remote name
        url: Remote URL

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.create_remote(name, url)
        return True, f'Remote {name} added'
    except GitCommandError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)
