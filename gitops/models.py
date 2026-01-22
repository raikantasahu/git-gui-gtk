"""Data models for git operations."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FileStatus(Enum):
    """File status in git repository."""
    MODIFIED = 'modified'
    ADDED = 'added'
    DELETED = 'deleted'
    RENAMED = 'renamed'
    COPIED = 'copied'
    UNTRACKED = 'untracked'
    UNMERGED = 'unmerged'


@dataclass
class FileChange:
    """Represents a changed file."""
    path: str
    status: FileStatus
    staged: bool
    old_path: Optional[str] = None  # For renames
