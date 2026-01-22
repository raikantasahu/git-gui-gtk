"""Get remotes operation."""

from typing import Optional

from git import Repo


def get_remotes(repo: Optional[Repo]) -> list[str]:
    """Get list of remote names.

    Args:
        repo: Git repository object

    Returns:
        List of remote names
    """
    if not repo:
        return []
    return [r.name for r in repo.remotes]
