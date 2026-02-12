"""Dialog modules for Git GUI GTK."""

from .push import show_push_dialog
from .pull import show_pull_dialog
from .fetch import show_fetch_dialog
from .add_remote import show_add_remote_dialog
from .rename_remote import show_rename_remote_dialog
from .delete_remote import show_delete_remote_dialog
from .list_remotes import show_list_remotes_dialog
from .create_branch import show_create_branch_dialog
from .checkout_branch import show_checkout_branch_dialog
from .rename_branch import show_rename_branch_dialog
from .delete_branch import show_delete_branch_dialog
from .reset_branch import show_reset_branch_dialog
from .merge import show_merge_dialog
from .rebase import show_rebase_dialog
from .database import (
    show_database_statistics_dialog,
    show_compress_database_dialog,
    show_verify_database_dialog,
)
from .ssh_key import show_ssh_key_dialog
from .about import show_about_dialog
from .open_repository import show_open_repository_dialog
from .message import show_message_dialog, MessageType
from .confirm import show_confirm_dialog
from .file_history import show_file_history_dialog

__all__ = [
    'show_push_dialog',
    'show_pull_dialog',
    'show_fetch_dialog',
    'show_add_remote_dialog',
    'show_rename_remote_dialog',
    'show_delete_remote_dialog',
    'show_list_remotes_dialog',
    'show_create_branch_dialog',
    'show_checkout_branch_dialog',
    'show_rename_branch_dialog',
    'show_delete_branch_dialog',
    'show_reset_branch_dialog',
    'show_merge_dialog',
    'show_rebase_dialog',
    'show_database_statistics_dialog',
    'show_compress_database_dialog',
    'show_verify_database_dialog',
    'show_ssh_key_dialog',
    'show_about_dialog',
    'show_open_repository_dialog',
    'show_message_dialog',
    'MessageType',
    'show_confirm_dialog',
    'show_file_history_dialog',
]
