"""Get remote branches operation."""

from typing import Optional

from git import Repo


def get_remote_branches(repo: Optional[Repo], remote_name: str) -> list[str]:
    """Get list of branches for a specific remote.

    Args:
        repo: Git repository object
        remote_name: Name of the remote

    Returns:
        List of branch names (without the remote/ prefix)
    """
    if not repo:
        return []
    try:
        branches = []
        prefix = f'refs/remotes/{remote_name}/'
        for ref in repo.refs:
            if ref.path.startswith(prefix):
                branch_name = ref.path[len(prefix):]
                if branch_name != 'HEAD':
                    branches.append(branch_name)
        return sorted(branches)
    except Exception:
        return []
