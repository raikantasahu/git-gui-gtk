"""Merge branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def merge_branch(
    repo: Optional[Repo],
    branch: str,
    strategy: str = 'default'
) -> tuple[bool, str]:
    """Merge a branch into the current branch.

    Args:
        repo: Git repository object
        branch: Branch to merge
        strategy: Merge strategy - one of 'default', 'no-ff', 'ff-only', 'squash'

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        args = []
        if strategy == 'no-ff':
            args.append('--no-ff')
        elif strategy == 'ff-only':
            args.append('--ff-only')
        elif strategy == 'squash':
            args.append('--squash')
        args.append(branch)
        repo.git.merge(*args)

        if strategy == 'squash':
            return True, f'Squashed {branch} into working tree. Please commit the changes.'
        return True, f'Merged {branch} successfully'
    except GitCommandError as e:
        return False, str(e)
