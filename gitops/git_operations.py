"""Main GitOperations class that delegates to individual operation modules."""

from typing import Optional, Callable

from git import Repo

from .models import FileChange, FileStatus
from . import open_repository as open_repo_mod
from . import get_repo_name as get_repo_name_mod
from . import get_current_branch as get_current_branch_mod
from . import get_status as get_status_mod
from . import get_diff as get_diff_mod
from . import stage_file as stage_file_mod
from . import unstage_file as unstage_file_mod
from . import stage_all as stage_all_mod
from . import unstage_all as unstage_all_mod
from . import commit as commit_mod
from . import get_last_commit_message as get_last_commit_message_mod
from . import get_last_commit_files as get_last_commit_files_mod
from . import get_tracking_remote as get_tracking_remote_mod
from . import push as push_mod
from . import get_remote_branches as get_remote_branches_mod
from . import pull as pull_mod
from . import fetch as fetch_mod
from . import revert_file as revert_file_mod
from . import get_branches as get_branches_mod
from . import create_branch as create_branch_mod
from . import checkout_branch as checkout_branch_mod
from . import delete_branch as delete_branch_mod
from . import rename_branch as rename_branch_mod
from . import reset_branch as reset_branch_mod
from . import merge_branch as merge_branch_mod
from . import rebase_branch as rebase_branch_mod
from . import get_remotes as get_remotes_mod
from . import get_remotes_with_urls as get_remotes_with_urls_mod
from . import add_remote as add_remote_mod
from . import rename_remote as rename_remote_mod
from . import delete_remote as delete_remote_mod
from . import get_log as get_log_mod
from . import get_database_statistics as get_database_statistics_mod
from . import compress_database as compress_database_mod
from . import verify_database as verify_database_mod


class GitOperations:
    """Wrapper class for git operations."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo: Optional[Repo] = None
        self.repo_path: Optional[str] = None
        if repo_path:
            self.open_repository(repo_path)

    def open_repository(self, path: str) -> bool:
        """Open a git repository at the given path."""
        self.repo, self.repo_path = open_repo_mod.open_repository(path)
        return self.repo is not None

    def is_valid(self) -> bool:
        """Check if repository is valid."""
        return self.repo is not None

    def get_repo_name(self) -> str:
        """Get repository name."""
        return get_repo_name_mod.get_repo_name(self.repo_path)

    def get_current_branch(self) -> str:
        """Get current branch name."""
        return get_current_branch_mod.get_current_branch(self.repo)

    def get_status(self) -> tuple[list[FileChange], list[FileChange]]:
        """Get repository status."""
        return get_status_mod.get_status(self.repo)

    def get_diff(self, path: str, staged: bool = False) -> str:
        """Get diff for a specific file."""
        return get_diff_mod.get_diff(self.repo, self.repo_path, path, staged)

    def stage_file(self, path: str) -> bool:
        """Stage a file for commit."""
        return stage_file_mod.stage_file(self.repo, path)

    def unstage_file(self, path: str) -> bool:
        """Unstage a file."""
        return unstage_file_mod.unstage_file(self.repo, path)

    def stage_all(self) -> bool:
        """Stage all changes."""
        return stage_all_mod.stage_all(self.repo)

    def unstage_all(self) -> bool:
        """Unstage all changes."""
        return unstage_all_mod.unstage_all(self.repo)

    def commit(self, message: str, amend: bool = False, sign_off: bool = False) -> tuple[bool, str]:
        """Create a commit."""
        return commit_mod.commit(self.repo, message, amend, sign_off)

    def get_last_commit_message(self) -> str:
        """Get the last commit message."""
        return get_last_commit_message_mod.get_last_commit_message(self.repo)

    def get_last_commit_files(self) -> list[FileChange]:
        """Get list of files changed in the last commit."""
        return get_last_commit_files_mod.get_last_commit_files(self.repo)

    def get_tracking_remote(self) -> Optional[str]:
        """Get the remote name for the current branch's tracking branch."""
        return get_tracking_remote_mod.get_tracking_remote(self.repo)

    def push(self, remote_name: str, branch_name: str = None,
             force: bool = False, tags: bool = False,
             progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
        """Push to remote."""
        return push_mod.push(self.repo, remote_name, branch_name, force, tags, progress_callback)

    def get_remote_branches(self, remote_name: str) -> list[str]:
        """Get list of branches for a specific remote."""
        return get_remote_branches_mod.get_remote_branches(self.repo, remote_name)

    def pull(self, remote_name: str, branch_name: str = None,
             ff_only: bool = False, rebase: bool = False,
             progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
        """Pull from remote."""
        return pull_mod.pull(self.repo, remote_name, branch_name, ff_only, rebase, progress_callback)

    def fetch(self, remote_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
        """Fetch from remote."""
        return fetch_mod.fetch(self.repo, remote_name, progress_callback)

    def revert_file(self, path: str) -> tuple[bool, str]:
        """Revert a file to its state in HEAD."""
        return revert_file_mod.revert_file(self.repo, path)

    def get_branches(self) -> list[str]:
        """Get list of local branches."""
        return get_branches_mod.get_branches(self.repo)

    def create_branch(self, name: str, checkout: bool = False) -> tuple[bool, str]:
        """Create a new branch."""
        return create_branch_mod.create_branch(self.repo, name, checkout)

    def checkout_branch(self, name: str) -> tuple[bool, str]:
        """Checkout a branch."""
        return checkout_branch_mod.checkout_branch(self.repo, name)

    def delete_branch(self, name: str, force: bool = False) -> tuple[bool, str]:
        """Delete a branch."""
        return delete_branch_mod.delete_branch(self.repo, name, force)

    def rename_branch(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """Rename a branch."""
        return rename_branch_mod.rename_branch(self.repo, old_name, new_name)

    def reset_branch(self, target: str, mode: str = 'mixed') -> tuple[bool, str]:
        """Reset current branch to a target commit."""
        return reset_branch_mod.reset_branch(self.repo, target, mode)

    def merge_branch(self, branch: str, no_ff: bool = False, squash: bool = False) -> tuple[bool, str]:
        """Merge a branch into the current branch."""
        return merge_branch_mod.merge_branch(self.repo, branch, no_ff, squash)

    def rebase_branch(self, onto: str) -> tuple[bool, str]:
        """Rebase current branch onto another branch."""
        return rebase_branch_mod.rebase_branch(self.repo, onto)

    def get_remotes(self) -> list[str]:
        """Get list of remote names."""
        return get_remotes_mod.get_remotes(self.repo)

    def get_remotes_with_urls(self) -> dict[str, str]:
        """Get dict of remote names to URLs."""
        return get_remotes_with_urls_mod.get_remotes_with_urls(self.repo)

    def add_remote(self, name: str, url: str) -> tuple[bool, str]:
        """Add a new remote."""
        return add_remote_mod.add_remote(self.repo, name, url)

    def rename_remote(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """Rename a remote."""
        return rename_remote_mod.rename_remote(self.repo, old_name, new_name)

    def delete_remote(self, name: str) -> tuple[bool, str]:
        """Delete a remote."""
        return delete_remote_mod.delete_remote(self.repo, name)

    def get_log(self, max_count: int = 50) -> list[dict]:
        """Get commit log."""
        return get_log_mod.get_log(self.repo, max_count)

    def get_database_statistics(self) -> tuple[bool, str]:
        """Get git database statistics."""
        return get_database_statistics_mod.get_database_statistics(self.repo)

    def compress_database(self) -> tuple[bool, str]:
        """Compress git database (git gc)."""
        return compress_database_mod.compress_database(self.repo)

    def verify_database(self) -> tuple[bool, str]:
        """Verify git database (git fsck)."""
        return verify_database_mod.verify_database(self.repo)
