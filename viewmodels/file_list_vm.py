"""FileListViewModel - manages file staging, unstaging, and revert operations."""

import gitops


class FileListViewModel:
    """ViewModel for file list operations (stage, unstage, revert).

    All methods operate on FileChange objects passed in by the View.
    The VM never accesses widgets directly.
    """

    def __init__(self, repo_vm):
        self._repo_vm = repo_vm

    def stage_file(self, file_change):
        """Stage a single file."""
        if gitops.stage_file(self._repo_vm.repo, file_change.path):
            self._repo_vm._status('Staged: ' + file_change.path)
            self._repo_vm.rescan()
        else:
            self._repo_vm._status('Failed to stage: ' + file_change.path, 'error')

    def unstage_file(self, file_change):
        """Unstage a single file."""
        if gitops.unstage_file(self._repo_vm.repo, file_change.path):
            self._repo_vm._status('Unstaged: ' + file_change.path)
            self._repo_vm.rescan()
        else:
            self._repo_vm._status('Failed to unstage: ' + file_change.path, 'error')

    def stage_all(self):
        """Stage all unstaged files."""
        if gitops.stage_all(self._repo_vm.repo):
            self._repo_vm._status('Staged all changes')
            self._repo_vm.rescan()
        else:
            self._repo_vm._status('Failed to stage all changes', 'error')

    def unstage_all(self):
        """Unstage all staged files."""
        if gitops.unstage_all(self._repo_vm.repo):
            self._repo_vm._status('Unstaged all changes')
            self._repo_vm.rescan()
        else:
            self._repo_vm._status('Failed to unstage all changes', 'error')

    def revert_file(self, path):
        """Execute the revert operation for a file path.

        The View is responsible for showing a confirmation dialog
        before calling this method.
        """
        success, message = gitops.revert_file(self._repo_vm.repo, path)
        self._repo_vm._status(message)
        self._repo_vm.rescan()
