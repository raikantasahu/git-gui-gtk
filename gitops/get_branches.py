"""Get branches operation."""

from typing import Optional

from git import Repo


def get_branches(repo: Optional[Repo]) -> list[str]:
    """Get list of local branches.

    Args:
        repo: Git repository object

    Returns:
        List of branch names
    """
    if not repo:
        return []
    return [b.name for b in repo.branches]
