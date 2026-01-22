"""Reset branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def reset_branch(repo: Optional[Repo], target: str, mode: str = 'mixed') -> tuple[bool, str]:
    """Reset current branch to a target commit.

    Args:
        repo: Git repository object
        target: Commit, branch, or tag to reset to
        mode: Reset mode - 'soft', 'mixed', or 'hard'

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        repo.git.reset(f'--{mode}', target)
        return True, f'Reset to {target} ({mode})'
    except GitCommandError as e:
        return False, str(e)
