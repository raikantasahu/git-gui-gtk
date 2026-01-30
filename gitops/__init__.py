"""Git operations module."""

from .models import FileStatus, FileChange

from .open_repository import open_repository
from .get_repo_name import get_repo_name
from .get_current_branch import get_current_branch
from .get_status import get_status
from .get_diff import get_diff
from .stage_file import stage_file
from .unstage_file import unstage_file
from .stage_all import stage_all
from .unstage_all import unstage_all
from .stage_hunk import stage_hunk
from .stage_lines import stage_lines
from .unstage_hunk import unstage_hunk
from .unstage_lines import unstage_lines
from .revert_hunk import revert_hunk
from .revert_lines import revert_lines
from .commit import commit
from .get_last_commit_message import get_last_commit_message
from .get_last_commit_files import get_last_commit_files
from .get_tracking_remote import get_tracking_remote
from .push import push
from .get_remote_branches import get_remote_branches
from .pull import pull
from .fetch import fetch
from .revert_file import revert_file
from .get_branches import get_branches
from .get_tracking_branches import get_tracking_branches
from .get_tags import get_tags
from .create_branch import create_branch
from .checkout_branch import checkout_branch
from .delete_branch import delete_branch
from .rename_branch import rename_branch
from .reset_branch import reset_branch
from .merge_branch import merge_branch
from .rebase_branch import rebase_branch
from .get_remotes import get_remotes
from .get_remotes_with_urls import get_remotes_with_urls
from .add_remote import add_remote
from .rename_remote import rename_remote
from .delete_remote import delete_remote
from .get_log import get_log
from .get_database_statistics import get_database_statistics
from .compress_database import compress_database
from .verify_database import verify_database

__all__ = [
    # Models
    'FileStatus',
    'FileChange',
    # Repository
    'open_repository',
    'get_repo_name',
    'get_current_branch',
    # Status and diff
    'get_status',
    'get_diff',
    # Staging
    'stage_file',
    'unstage_file',
    'stage_all',
    'unstage_all',
    'stage_hunk',
    'stage_lines',
    'unstage_hunk',
    'unstage_lines',
    # Commit
    'commit',
    'get_last_commit_message',
    'get_last_commit_files',
    # Remote operations
    'get_tracking_remote',
    'push',
    'get_remote_branches',
    'pull',
    'fetch',
    'get_remotes',
    'get_remotes_with_urls',
    'add_remote',
    'rename_remote',
    'delete_remote',
    # File operations
    'revert_file',
    'revert_hunk',
    'revert_lines',
    # Branch operations
    'get_branches',
    'get_tracking_branches',
    'get_tags',
    'create_branch',
    'checkout_branch',
    'delete_branch',
    'rename_branch',
    'reset_branch',
    'merge_branch',
    'rebase_branch',
    # Log
    'get_log',
    # Database
    'get_database_statistics',
    'compress_database',
    'verify_database',
]
