"""Get diff for a specific commit."""

from typing import Optional

from git import Repo


def get_commit_diff(repo: Optional[Repo], commit_hash: str) -> str:
    """Get the full diff text for a commit.

    Args:
        repo: Git repository object
        commit_hash: The commit hash to get the diff for

    Returns:
        Diff text string
    """
    if not repo:
        return ''

    try:
        return repo.git.show('--format=', commit_hash)
    except Exception:
        return ''
