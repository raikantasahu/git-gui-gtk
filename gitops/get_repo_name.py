"""Get repository name operation."""

import os
from typing import Optional


def get_repo_name(repo_path: Optional[str]) -> str:
    """Get repository name.

    Args:
        repo_path: Path to the repository

    Returns:
        Repository name or empty string
    """
    if not repo_path:
        return ''
    return os.path.basename(repo_path)
