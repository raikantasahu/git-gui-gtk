"""Get current branch operation."""

from typing import Optional

from git import Repo


def get_current_branch(repo: Optional[Repo]) -> str:
    """Get current branch name.

    Args:
        repo: Git repository object

    Returns:
        Branch name or empty string
    """
    if not repo:
        return ''
    try:
        return repo.active_branch.name
    except TypeError:
        # Detached HEAD state
        return f'({repo.head.commit.hexsha[:7]})'
