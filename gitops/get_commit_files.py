"""Get list of files changed in a specific commit."""

from typing import Optional

from git import Repo


def get_commit_files(repo: Optional[Repo], commit_hash: str) -> list[tuple[str, str]]:
    """Get the list of files changed in a commit with their status.

    Args:
        repo: Git repository object
        commit_hash: The commit hash

    Returns:
        List of (status, file_path) tuples where status is one of:
        A (added), M (modified), D (deleted), R (renamed), C (copied).
        For renames/copies the path is "old_path -> new_path".
    """
    if not repo:
        return []

    try:
        output = repo.git.diff_tree(
            '--no-commit-id', '--root', '-r', '--name-status', commit_hash
        )
        files = []
        for line in output.strip().splitlines():
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            status = parts[0][0]
            if len(parts) == 3:
                # Rename or copy: old_path -> new_path
                path = f'{parts[1]} -> {parts[2]}'
            else:
                path = parts[1]
            files.append((status, path))
        return files
    except Exception:
        return []
