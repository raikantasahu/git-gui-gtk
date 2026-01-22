"""Rebase branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def rebase_branch(repo: Optional[Repo], onto: str) -> tuple[bool, str]:
    """Rebase current branch onto another branch.

    Args:
        repo: Git repository object
        onto: Branch to rebase onto

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.rebase(onto)
        return True, f'Rebased onto {onto} successfully'
    except GitCommandError as e:
        return False, str(e)
