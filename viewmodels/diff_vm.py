"""DiffViewModel - manages diff display, hunk/line staging, and revert operations."""

import gitops
from gitops import FileStatus


_STATUS_MAP = {
    FileStatus.MODIFIED: 'Modified, not staged',
    FileStatus.ADDED: 'Added, not staged',
    FileStatus.DELETED: 'Missing',
    FileStatus.RENAMED: 'Renamed, not staged',
    FileStatus.COPIED: 'Copied, not staged',
    FileStatus.UNTRACKED: 'Untracked, not staged',
    FileStatus.UNMERGED: 'Unmerged',
}


class DiffViewModel:
    """ViewModel for diff display and hunk/line operations.

    After calling show_diff(), the View reads the result attributes
    (diff_text, file_path, status_text, is_staged, is_untracked)
    to update its widgets.

    Attributes:
        diff_text: the diff content (str)
        file_path: path of the file being diffed (str)
        status_text: human-readable status (str)
        is_staged: whether the file is staged (bool)
        is_untracked: whether the file is untracked (bool)
        context_lines: number of context lines (int)
        current_file: the FileChange currently being displayed, or None
    """

    def __init__(self, repo_vm):
        self._repo_vm = repo_vm
        self.diff_text = ''
        self.file_path = ''
        self.status_text = ''
        self.is_staged = False
        self.is_untracked = False
        self.context_lines = 3
        self.current_file = None
        self._current_diff_staged = False

    def show_diff(self, file_change, staged, context_lines=None):
        """Compute diff for a file and store the results.

        The View should read diff_text, file_path, status_text,
        is_staged, is_untracked after calling this method.
        """
        if context_lines is not None:
            self.context_lines = context_lines

        self.diff_text = gitops.get_diff(
            self._repo_vm.repo, self._repo_vm.repo_path, file_change.path,
            staged=staged, context_lines=self.context_lines
        )
        self.file_path = file_change.path
        self.status_text = self._get_file_status_text(file_change, staged)
        self.is_staged = staged
        self.is_untracked = file_change.status == FileStatus.UNTRACKED
        self.current_file = file_change
        self._current_diff_staged = staged

    def clear(self):
        """Clear the current diff state."""
        self.diff_text = ''
        self.file_path = ''
        self.status_text = ''
        self.is_staged = False
        self.is_untracked = False
        self.current_file = None
        self._current_diff_staged = False

    def refresh(self):
        """Refresh the current diff with current context_lines.

        Returns True if there was a diff to refresh, False otherwise.
        """
        if self.current_file:
            self.show_diff(self.current_file, self._current_diff_staged)
            return True
        return False

    def is_stale(self, unstaged_files, staged_files):
        """Check if the currently displayed file is no longer in the file lists.

        Returns True if the diff is stale and should be cleared.
        """
        if not self.current_file:
            return False
        all_paths = [f.path for f in unstaged_files + staged_files]
        return self.current_file.path not in all_paths

    def stage_hunk(self, file_path, line):
        """Stage a hunk at the given diff line."""
        success, message = gitops.stage_hunk(self._repo_vm.repo, file_path, line)
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()

    def stage_lines(self, file_path, start_line, end_line):
        """Stage lines in the given diff line range."""
        success, message = gitops.stage_lines(
            self._repo_vm.repo, file_path, start_line, end_line, self.context_lines
        )
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()

    def unstage_hunk(self, file_path, line):
        """Unstage a hunk at the given diff line."""
        success, message = gitops.unstage_hunk(self._repo_vm.repo, file_path, line)
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()

    def unstage_lines(self, file_path, start_line, end_line):
        """Unstage lines in the given diff line range."""
        success, message = gitops.unstage_lines(
            self._repo_vm.repo, file_path, start_line, end_line, self.context_lines
        )
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()

    def revert_hunk(self, file_path, line):
        """Revert a hunk. View must confirm before calling."""
        success, message = gitops.revert_hunk(self._repo_vm.repo, file_path, line)
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()

    def revert_lines(self, file_path, start_line, end_line):
        """Revert lines. View must confirm before calling."""
        success, message = gitops.revert_lines(
            self._repo_vm.repo, file_path, start_line, end_line, self.context_lines
        )
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()

    @staticmethod
    def _get_file_status_text(file_change, staged):
        """Get descriptive status text for a file."""
        if staged:
            return 'Staged for commit'
        return _STATUS_MAP.get(file_change.status, 'Unknown')
