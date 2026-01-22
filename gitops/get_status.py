"""Get repository status operation."""

from typing import Optional

from git import Repo

from .models import FileChange, FileStatus
from ._utils import diff_to_status


def get_status(repo: Optional[Repo]) -> tuple[list[FileChange], list[FileChange]]:
    """Get repository status.

    Args:
        repo: Git repository object

    Returns:
        Tuple of (unstaged_changes, staged_changes)
    """
    if not repo:
        return [], []

    unstaged = []
    staged = []

    # Get staged changes (index vs HEAD)
    try:
        staged_diffs = repo.index.diff('HEAD')
        for diff in staged_diffs:
            status = diff_to_status(diff)
            old_path = diff.a_path if diff.renamed else None
            path = diff.b_path if diff.b_path else diff.a_path
            staged.append(FileChange(
                path=path,
                status=status,
                staged=True,
                old_path=old_path
            ))
    except Exception:
        # Empty repo (no HEAD)
        pass

    # Get new files staged
    try:
        for entry in repo.index.entries:
            path = entry[0]
            # Check if file is new (not in HEAD)
            try:
                repo.head.commit.tree[path]
            except (KeyError, ValueError):
                # File is new
                if not any(f.path == path for f in staged):
                    staged.append(FileChange(
                        path=path,
                        status=FileStatus.ADDED,
                        staged=True
                    ))
    except Exception:
        pass

    # Get unstaged changes (working tree vs index)
    unstaged_diffs = repo.index.diff(None)
    for diff in unstaged_diffs:
        status = diff_to_status(diff)
        path = diff.a_path if diff.a_path else diff.b_path
        unstaged.append(FileChange(
            path=path,
            status=status,
            staged=False
        ))

    # Get untracked files
    for path in repo.untracked_files:
        unstaged.append(FileChange(
            path=path,
            status=FileStatus.UNTRACKED,
            staged=False
        ))

    return unstaged, staged
