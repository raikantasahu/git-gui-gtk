"""Git operations wrapper using GitPython."""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

from git import Repo, InvalidGitRepositoryError, GitCommandError
from git.diff import Diff


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


class GitOperations:
    """Wrapper class for git operations."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo: Optional[Repo] = None
        self.repo_path: Optional[str] = None
        if repo_path:
            self.open_repository(repo_path)

    def open_repository(self, path: str) -> bool:
        """Open a git repository at the given path."""
        try:
            # Check if path is a git repo or contains one
            if os.path.isdir(os.path.join(path, '.git')):
                self.repo = Repo(path)
            else:
                # Try to find a repo in parent directories
                self.repo = Repo(path, search_parent_directories=True)
            self.repo_path = self.repo.working_dir
            return True
        except InvalidGitRepositoryError:
            self.repo = None
            self.repo_path = None
            return False

    def is_valid(self) -> bool:
        """Check if repository is valid."""
        return self.repo is not None

    def get_repo_name(self) -> str:
        """Get repository name."""
        if not self.repo_path:
            return ''
        return os.path.basename(self.repo_path)

    def get_current_branch(self) -> str:
        """Get current branch name."""
        if not self.repo:
            return ''
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            return f'({self.repo.head.commit.hexsha[:7]})'

    def get_status(self) -> tuple[list[FileChange], list[FileChange]]:
        """Get repository status.

        Returns:
            Tuple of (unstaged_changes, staged_changes)
        """
        if not self.repo:
            return [], []

        unstaged = []
        staged = []

        # Get staged changes (index vs HEAD)
        try:
            staged_diffs = self.repo.index.diff('HEAD')
            for diff in staged_diffs:
                status = self._diff_to_status(diff)
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
            for entry in self.repo.index.entries:
                path = entry[0]
                # Check if file is new (not in HEAD)
                try:
                    self.repo.head.commit.tree[path]
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
        unstaged_diffs = self.repo.index.diff(None)
        for diff in unstaged_diffs:
            status = self._diff_to_status(diff)
            path = diff.a_path if diff.a_path else diff.b_path
            unstaged.append(FileChange(
                path=path,
                status=status,
                staged=False
            ))

        # Get untracked files
        for path in self.repo.untracked_files:
            unstaged.append(FileChange(
                path=path,
                status=FileStatus.UNTRACKED,
                staged=False
            ))

        return unstaged, staged

    def _diff_to_status(self, diff: Diff) -> FileStatus:
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

    def get_diff(self, path: str, staged: bool = False) -> str:
        """Get diff for a specific file.

        Args:
            path: File path relative to repo root
            staged: If True, show staged diff (index vs HEAD)
                   If False, show unstaged diff (working tree vs index)
        """
        if not self.repo:
            return ''

        try:
            if staged:
                # Staged: compare index to HEAD
                diff = self.repo.git.diff('--cached', '--', path)
            else:
                # Check if file is untracked
                if path in self.repo.untracked_files:
                    # Show entire file content as new
                    full_path = os.path.join(self.repo_path, path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', errors='replace') as f:
                            content = f.read()
                        lines = content.split('\n')
                        diff_lines = [f'diff --git a/{path} b/{path}',
                                     'new file mode 100644',
                                     '--- /dev/null',
                                     f'+++ b/{path}',
                                     f'@@ -0,0 +1,{len(lines)} @@']
                        for line in lines:
                            diff_lines.append(f'+{line}')
                        return '\n'.join(diff_lines)
                    return ''
                else:
                    # Unstaged: compare working tree to index
                    diff = self.repo.git.diff('--', path)
            return diff
        except GitCommandError as e:
            return f'Error getting diff: {e}'

    def stage_file(self, path: str) -> bool:
        """Stage a file for commit."""
        if not self.repo:
            return False
        try:
            self.repo.index.add([path])
            return True
        except Exception:
            return False

    def unstage_file(self, path: str) -> bool:
        """Unstage a file."""
        if not self.repo:
            return False
        try:
            # Reset file in index to HEAD state
            self.repo.git.reset('HEAD', '--', path)
            return True
        except GitCommandError:
            # Might be a new file, try removing from index
            try:
                self.repo.index.remove([path], working_tree=False)
                return True
            except Exception:
                return False

    def stage_all(self) -> bool:
        """Stage all changes."""
        if not self.repo:
            return False
        try:
            self.repo.git.add('-A')
            return True
        except GitCommandError:
            return False

    def unstage_all(self) -> bool:
        """Unstage all changes."""
        if not self.repo:
            return False
        try:
            self.repo.git.reset('HEAD')
            return True
        except GitCommandError:
            return False

    def commit(self, message: str, amend: bool = False, sign_off: bool = False) -> tuple[bool, str]:
        """Create a commit.

        Args:
            message: Commit message
            amend: If True, amend the last commit
            sign_off: If True, add Signed-off-by line

        Returns:
            Tuple of (success, message/error)
        """
        if not self.repo:
            return False, 'No repository open'

        if not message.strip() and not amend:
            return False, 'Empty commit message'

        try:
            args = []
            if amend:
                args.append('--amend')
            if sign_off:
                args.append('--signoff')
            args.extend(['-m', message])

            self.repo.git.commit(*args)
            return True, 'Commit successful'
        except GitCommandError as e:
            return False, str(e)

    def get_last_commit_message(self) -> str:
        """Get the last commit message."""
        if not self.repo:
            return ''
        try:
            return self.repo.head.commit.message
        except Exception:
            return ''

    def get_last_commit_files(self) -> list[FileChange]:
        """Get list of files changed in the last commit."""
        if not self.repo:
            return []
        try:
            commit = self.repo.head.commit
            parent = commit.parents[0] if commit.parents else None

            files = []
            if parent:
                # Compare with parent commit
                diffs = parent.diff(commit)
            else:
                # Initial commit - all files are new
                diffs = commit.diff(None, R=True)

            for diff in diffs:
                status = self._diff_to_status(diff)
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

    def get_tracking_remote(self) -> Optional[str]:
        """Get the remote name for the current branch's tracking branch.

        Returns:
            Remote name or None if no tracking branch is set
        """
        if not self.repo:
            return None
        try:
            branch = self.repo.active_branch
            tracking = branch.tracking_branch()
            if tracking:
                # tracking.remote_name gives the remote
                return tracking.remote_name
        except (TypeError, AttributeError):
            pass
        return None

    def push(self, remote_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
        """Push to remote.

        Args:
            remote_name: Name of the remote to push to

        Returns:
            Tuple of (success, message/error)
        """
        if not self.repo:
            return False, 'No repository open'

        try:
            remote = self.repo.remote(remote_name)
            push_info = remote.push()

            if push_info:
                info = push_info[0]
                if info.flags & info.ERROR:
                    return False, f'Push failed: {info.summary}'
                return True, f'Push to {remote_name} successful'
            return True, f'Push to {remote_name} successful'
        except GitCommandError as e:
            return False, str(e)
        except ValueError as e:
            return False, f'Remote not found: {e}'

    def pull(self, remote_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
        """Pull from remote.

        Args:
            remote_name: Name of the remote to pull from

        Returns:
            Tuple of (success, message/error)
        """
        if not self.repo:
            return False, 'No repository open'

        try:
            remote = self.repo.remote(remote_name)
            remote.pull()
            return True, f'Pull from {remote_name} successful'
        except GitCommandError as e:
            return False, str(e)
        except ValueError as e:
            return False, f'Remote not found: {e}'

    def fetch(self, remote_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> tuple[bool, str]:
        """Fetch from remote.

        Args:
            remote_name: Name of the remote to fetch from

        Returns:
            Tuple of (success, message/error)
        """
        if not self.repo:
            return False, 'No repository open'

        try:
            remote = self.repo.remote(remote_name)
            remote.fetch()
            return True, f'Fetch from {remote_name} successful'
        except GitCommandError as e:
            return False, str(e)
        except ValueError as e:
            return False, f'Remote not found: {e}'

    def revert_file(self, path: str) -> tuple[bool, str]:
        """Revert a file to its state in HEAD.

        Returns:
            Tuple of (success, message/error)
        """
        if not self.repo:
            return False, 'No repository open'

        try:
            self.repo.git.checkout('HEAD', '--', path)
            return True, f'Reverted {path}'
        except GitCommandError as e:
            return False, str(e)

    def get_branches(self) -> list[str]:
        """Get list of local branches."""
        if not self.repo:
            return []
        return [b.name for b in self.repo.branches]

    def create_branch(self, name: str, checkout: bool = False) -> tuple[bool, str]:
        """Create a new branch.

        Args:
            name: Branch name
            checkout: If True, checkout the branch after creation
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.create_head(name)
            if checkout:
                self.repo.git.checkout(name)
                return True, f'Branch {name} created and checked out'
            return True, f'Branch {name} created'
        except GitCommandError as e:
            return False, str(e)

    def checkout_branch(self, name: str) -> tuple[bool, str]:
        """Checkout a branch."""
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.git.checkout(name)
            return True, f'Switched to branch {name}'
        except GitCommandError as e:
            return False, str(e)

    def delete_branch(self, name: str, force: bool = False) -> tuple[bool, str]:
        """Delete a branch."""
        if not self.repo:
            return False, 'No repository open'
        try:
            flag = '-D' if force else '-d'
            self.repo.git.branch(flag, name)
            return True, f'Branch {name} deleted'
        except GitCommandError as e:
            return False, str(e)

    def rename_branch(self, old_name: str, new_name: str) -> tuple[bool, str]:
        """Rename a branch.

        Args:
            old_name: Current branch name
            new_name: New branch name
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.git.branch('-m', old_name, new_name)
            return True, f'Branch {old_name} renamed to {new_name}'
        except GitCommandError as e:
            return False, str(e)

    def reset_branch(self, target: str, mode: str = 'mixed') -> tuple[bool, str]:
        """Reset current branch to a target commit.

        Args:
            target: Commit, branch, or tag to reset to
            mode: Reset mode - 'soft', 'mixed', or 'hard'
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.git.reset(f'--{mode}', target)
            return True, f'Reset to {target} ({mode})'
        except GitCommandError as e:
            return False, str(e)

    def merge_branch(self, branch: str, no_ff: bool = False, squash: bool = False) -> tuple[bool, str]:
        """Merge a branch into the current branch.

        Args:
            branch: Branch to merge
            no_ff: If True, always create a merge commit
            squash: If True, squash all commits into one
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            args = [branch]
            if no_ff:
                args.insert(0, '--no-ff')
            if squash:
                args.insert(0, '--squash')
            self.repo.git.merge(*args)
            return True, f'Merged {branch} successfully'
        except GitCommandError as e:
            return False, str(e)

    def rebase_branch(self, onto: str) -> tuple[bool, str]:
        """Rebase current branch onto another branch.

        Args:
            onto: Branch to rebase onto
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.git.rebase(onto)
            return True, f'Rebased onto {onto} successfully'
        except GitCommandError as e:
            return False, str(e)

    def get_remotes(self) -> list[str]:
        """Get list of remote names."""
        if not self.repo:
            return []
        return [r.name for r in self.repo.remotes]

    def get_remotes_with_urls(self) -> dict[str, str]:
        """Get dict of remote names to URLs."""
        if not self.repo:
            return {}
        return {r.name: r.url for r in self.repo.remotes}

    def add_remote(self, name: str, url: str) -> tuple[bool, str]:
        """Add a new remote.

        Args:
            name: Remote name
            url: Remote URL
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.create_remote(name, url)
            return True, f'Remote {name} added'
        except GitCommandError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def get_log(self, max_count: int = 50) -> list[dict]:
        """Get commit log.

        Returns:
            List of commit dicts with keys: hash, short_hash, author, date, message
        """
        if not self.repo:
            return []

        commits = []
        try:
            for commit in self.repo.iter_commits(max_count=max_count):
                commits.append({
                    'hash': commit.hexsha,
                    'short_hash': commit.hexsha[:7],
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat(),
                    'message': commit.message.strip()
                })
        except Exception:
            pass
        return commits

    def get_database_statistics(self) -> tuple[bool, str]:
        """Get git database statistics.

        Returns:
            Tuple of (success, output/error)
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            output = self.repo.git.count_objects('-v')
            return True, output
        except GitCommandError as e:
            return False, str(e)

    def compress_database(self) -> tuple[bool, str]:
        """Compress git database (git gc).

        Returns:
            Tuple of (success, message/error)
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            self.repo.git.gc()
            return True, 'Database compressed successfully'
        except GitCommandError as e:
            return False, str(e)

    def verify_database(self) -> tuple[bool, str]:
        """Verify git database (git fsck).

        Returns:
            Tuple of (success, output/error)
        """
        if not self.repo:
            return False, 'No repository open'
        try:
            output = self.repo.git.fsck()
            return True, output
        except GitCommandError as e:
            return False, str(e)
