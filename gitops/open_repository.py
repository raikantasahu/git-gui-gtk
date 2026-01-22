"""Open repository operation."""

import os
from typing import Optional

from git import Repo, InvalidGitRepositoryError


def open_repository(path: str) -> tuple[Optional[Repo], Optional[str]]:
    """Open a git repository at the given path.

    Args:
        path: Path to the repository

    Returns:
        Tuple of (Repo object, repo_path) or (None, None) if invalid
    """
    try:
        # Check if path is a git repo or contains one
        if os.path.isdir(os.path.join(path, '.git')):
            repo = Repo(path)
        else:
            # Try to find a repo in parent directories
            repo = Repo(path, search_parent_directories=True)
        return repo, repo.working_dir
    except InvalidGitRepositoryError:
        return None, None
