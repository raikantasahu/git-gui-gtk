"""Get current branch operation."""

from typing import Optional

from git import Repo


def get_current_branch(repo: Optional[Repo]) -> str:
    """Get current branch name.

    Args:
        repo: Git repository object

    Returns:
        Branch name, or detached HEAD info
    """
    if not repo:
        return ''
    try:
        return repo.active_branch.name
    except TypeError:
        # Detached HEAD state - try to find what we're detached at
        head_commit = repo.head.commit
        short_sha = head_commit.hexsha[:7]

        # Check if HEAD matches any tag
        for tag in repo.tags:
            if tag.commit == head_commit:
                return f'HEAD detached at {tag.name}'

        # Check if HEAD matches any remote tracking branch
        for ref in repo.refs:
            if ref.path.startswith('refs/remotes/') and ref.commit == head_commit:
                # Extract remote/branch name (e.g., "origin/main")
                tracking_name = ref.path[len('refs/remotes/'):]
                return f'HEAD detached at {tracking_name}'

        # Fall back to showing the commit hash
        return f'HEAD detached at {short_sha}'
