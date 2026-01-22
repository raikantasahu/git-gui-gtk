"""Get tracking remote operation."""

from typing import Optional

from git import Repo


def get_tracking_remote(repo: Optional[Repo]) -> Optional[str]:
    """Get the remote name for the current branch's tracking branch.

    Args:
        repo: Git repository object

    Returns:
        Remote name or None if no tracking branch is set
    """
    if not repo:
        return None
    try:
        branch = repo.active_branch
        tracking = branch.tracking_branch()
        if tracking:
            # tracking.remote_name gives the remote
            return tracking.remote_name
    except (TypeError, AttributeError):
        pass
    return None
