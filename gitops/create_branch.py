"""Create branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def create_branch(repo: Optional[Repo], name: str, checkout: bool = False) -> tuple[bool, str]:
    """Create a new branch.

    Args:
        repo: Git repository object
        name: Branch name
        checkout: If True, checkout the branch after creation

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.create_head(name)
        if checkout:
            repo.git.checkout(name)
            return True, f'Branch {name} created and checked out'
        return True, f'Branch {name} created'
    except GitCommandError as e:
        return False, str(e)
