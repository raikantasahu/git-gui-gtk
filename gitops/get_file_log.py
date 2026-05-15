"""Get file log operation."""

from typing import Optional

from git import Repo


def get_file_log(repo: Optional[Repo], file_path: str, max_count: int = 50,
                 skip: int = 0) -> list[dict]:
    """Get commit log for a specific file.

    Args:
        repo: Git repository object
        file_path: Path to the file (relative to repo root)
        max_count: Maximum number of commits to return
        skip: Number of commits to skip from the start of the history

    Returns:
        List of commit dicts with keys: hash, short_hash, author, date, message
    """
    if not repo:
        return []

    commits = []
    try:
        for commit in repo.iter_commits(max_count=max_count, paths=file_path, skip=skip):
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
