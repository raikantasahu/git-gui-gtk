"""Get tags operation."""

from typing import Optional

from git import Repo


def get_tags(repo: Optional[Repo]) -> list[str]:
    """Get list of tags.

    Args:
        repo: Git repository object

    Returns:
        List of tag names
    """
    if not repo:
        return []
    try:
        return sorted([t.name for t in repo.tags])
    except Exception:
        return []
