"""Pull operation."""

from typing import Optional, Callable

from git import Repo, GitCommandError


def pull(repo: Optional[Repo], remote_name: str, branch_name: str = None,
         ff_only: bool = False, rebase: bool = False,
         progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
    """Pull from remote.

    Args:
        repo: Git repository object
        remote_name: Name of the remote to pull from
        branch_name: Name of the remote branch to pull (optional)
        ff_only: If True, use --ff-only option
        rebase: If True, use --rebase option
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'

    try:
        args = []
        if ff_only:
            args.append('--ff-only')
        elif rebase:
            args.append('--rebase')

        if branch_name:
            args.extend([remote_name, branch_name])
        else:
            args.append(remote_name)

        repo.git.pull(*args)
        return True, f'Pull from {remote_name}/{branch_name or ""} successful'
    except GitCommandError as e:
        return False, str(e)
    except ValueError as e:
        return False, f'Remote not found: {e}'
