"""Create branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def create_branch(
    repo: Optional[Repo],
    name: str,
    start_point: Optional[str] = None,
    checkout: bool = False
) -> tuple[bool, str]:
    """Create a new branch.

    Args:
        repo: Git repository object
        name: Branch name
        start_point: Starting point (branch, tag, or commit). If None, uses HEAD.
        checkout: If True, checkout the branch after creation

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        if start_point:
            repo.create_head(name, start_point)
        else:
            repo.create_head(name)
        if checkout:
            repo.git.checkout(name)
            return True, f'Branch {name} created and checked out'
        return True, f'Branch {name} created'
    except GitCommandError as e:
        return False, str(e)
