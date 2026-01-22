"""Push operation."""

from typing import Optional, Callable

from git import Repo, GitCommandError


def push(repo: Optional[Repo], remote_name: str, branch_name: str = None,
         force: bool = False, tags: bool = False,
         progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
    """Push to remote.

    Args:
        repo: Git repository object
        remote_name: Name of the remote to push to
        branch_name: Name of the branch to push (optional)
        force: If True, use --force option
        tags: If True, use --tags option
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'

    try:
        args = []
        if force:
            args.append('--force')
        if tags:
            args.append('--tags')

        args.append(remote_name)
        if branch_name:
            args.append(branch_name)

        repo.git.push(*args)
        branch_display = f'{remote_name}/{branch_name}' if branch_name else remote_name
        return True, f'Push to {branch_display} successful'
    except GitCommandError as e:
        return False, str(e)
    except ValueError as e:
        return False, f'Remote not found: {e}'
