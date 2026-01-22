"""Commit operation."""

from typing import Optional

from git import Repo, GitCommandError


def commit(repo: Optional[Repo], message: str, amend: bool = False, sign_off: bool = False) -> tuple[bool, str]:
    """Create a commit.

    Args:
        repo: Git repository object
        message: Commit message
        amend: If True, amend the last commit
        sign_off: If True, add Signed-off-by line

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'

    if not message.strip() and not amend:
        return False, 'Empty commit message'

    try:
        args = []
        if amend:
            args.append('--amend')
        if sign_off:
            args.append('--signoff')
        args.extend(['-m', message])

        repo.git.commit(*args)
        return True, 'Commit successful'
    except GitCommandError as e:
        return False, str(e)
