"""Delete branch operation."""

from typing import Optional

from git import Repo, GitCommandError


def delete_branch(repo: Optional[Repo], name: str, force: bool = False) -> tuple[bool, str]:
    """Delete a branch.

    Args:
        repo: Git repository object
        name: Branch name to delete
        force: If True, force delete even if not merged

    Returns:
        Tuple of (success, message/error)
    """
    if not repo:
        return False, 'No repository open'
    try:
        flag = '-D' if force else '-d'
        repo.git.branch(flag, name)
        return True, f'Branch {name} deleted'
    except GitCommandError as e:
        return False, str(e)
