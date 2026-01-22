"""Get log operation."""

from typing import Optional

from git import Repo


def get_log(repo: Optional[Repo], max_count: int = 50) -> list[dict]:
    """Get commit log.

    Args:
        repo: Git repository object
        max_count: Maximum number of commits to return

    Returns:
        List of commit dicts with keys: hash, short_hash, author, date, message
    """
    if not repo:
        return []

    commits = []
    try:
        for commit in repo.iter_commits(max_count=max_count):
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
