"""Get remotes with URLs operation."""

from typing import Optional

from git import Repo


def get_remotes_with_urls(repo: Optional[Repo]) -> dict[str, str]:
    """Get dict of remote names to URLs.

    Args:
        repo: Git repository object

    Returns:
        Dict mapping remote names to URLs
    """
    if not repo:
        return {}
    return {r.name: r.url for r in repo.remotes}
