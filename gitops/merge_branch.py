"""Merge branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def merge_branch(repo: Optional[Repo], branch: str, no_ff: bool = False, squash: bool = False) -> tuple[bool, str]:
    """Merge a branch into the current branch.

    Args:
        repo: Git repository object
        branch: Branch to merge
        no_ff: If True, always create a merge commit
        squash: If True, squash all commits into one

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        args = [branch]
        if no_ff:
            args.insert(0, '--no-ff')
        if squash:
            args.insert(0, '--squash')
        repo.git.merge(*args)
        return True, f'Merged {branch} successfully'
    except GitCommandError as e:
        return False, str(e)
