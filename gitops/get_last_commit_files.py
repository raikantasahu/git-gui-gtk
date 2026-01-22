"""Get last commit files operation."""

from typing import Optional

from git import Repo

from .models import FileChange
from ._utils import diff_to_status


def get_last_commit_files(repo: Optional[Repo]) -> list[FileChange]:
    """Get list of files changed in the last commit.

    Args:
        repo: Git repository object

    Returns:
        List of FileChange objects
    """
    if not repo:
        return []
    try:
        commit = repo.head.commit
        parent = commit.parents[0] if commit.parents else None

        files = []
        if parent:
            # Compare with parent commit
            diffs = parent.diff(commit)
        else:
            # Initial commit - all files are new
            diffs = commit.diff(None, R=True)

        for diff in diffs:
            status = diff_to_status(diff)
            path = diff.b_path if diff.b_path else diff.a_path
            old_path = diff.a_path if diff.renamed else None
            files.append(FileChange(
                path=path,
                status=status,
                staged=True,
                old_path=old_path
            ))
        return files
    except Exception:
        return []
