"""Shared utility functions for git operations (not exported)."""

from git.diff import Diff

from .models import FileStatus


def diff_to_status(diff: Diff) -> FileStatus:
    """Convert git diff to FileStatus."""
    if diff.new_file:
        return FileStatus.ADDED
    elif diff.deleted_file:
        return FileStatus.DELETED
    elif diff.renamed:
        return FileStatus.RENAMED
    elif diff.copied_file:
        return FileStatus.COPIED
    else:
        return FileStatus.MODIFIED
