"""Get tracking branches operation."""

from typing import Optional

from git import Repo


def get_tracking_branches(repo: Optional[Repo]) -> list[str]:
    """Get list of all remote tracking branches.

    Args:
        repo: Git repository object

    Returns:
        List of tracking branch names (e.g., 'origin/main', 'upstream/develop')
    """
    if not repo:
        return []
    try:
        branches = []
        prefix = 'refs/remotes/'
        for ref in repo.refs:
            if ref.path.startswith(prefix):
                branch_name = ref.path[len(prefix):]
                if not branch_name.endswith('/HEAD'):
                    branches.append(branch_name)
        return sorted(branches)
    except Exception:
        return []
