"""Get log operation."""

from typing import Optional

from git import Repo


def get_log(repo: Optional[Repo], max_count: int = 50, branch: Optional[str] = None,
            skip: int = 0) -> list[dict]:
    """Get commit log.

    Args:
        repo: Git repository object
        max_count: Maximum number of commits to return
        branch: Branch name to show log for (None for current branch)
        skip: Number of commits to skip from the start of the history

    Returns:
        List of commit dicts with keys: hash, short_hash, author, date, message
    """
    if not repo:
        return []

    commits = []
    try:
        rev = branch if branch else None
        for commit in repo.iter_commits(rev=rev, max_count=max_count, skip=skip):
            commits.append({
                'hash': commit.hexsha,
                'short_hash': commit.hexsha[:7],
                'author': str(commit.author),
                'date': commit.committed_datetime.isoformat(),
                'message': commit.message.strip()
            })
    except Exception:
        pass
    return commits
