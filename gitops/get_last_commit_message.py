"""Get last commit message operation."""

from typing import Optional

from git import Repo


def get_last_commit_message(repo: Optional[Repo]) -> str:
    """Get the last commit message.

    Args:
        repo: Git repository object

    Returns:
        Last commit message or empty string
    """
    if not repo:
        return ''
    try:
        return repo.head.commit.message
    except Exception:
        return ''
