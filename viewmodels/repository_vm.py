"""RepositoryViewModel - manages repository lifecycle, scanning, and status."""

import gitops


class RepositoryViewModel:
    """ViewModel for repository-level state and operations.

    Attributes:
        repo: git.Repo instance or None
        repo_path: absolute path to the repo (str)
        repo_name: display name (str)
        branch_name: current branch (str)
        unstaged_files: list of FileChange
        staged_files: list of FileChange
        has_staged_files: bool

    Callbacks (set by the View):
        on_state_changed: called after any state mutation (rescan, open, close)
        set_status: called with (message, msg_type) to display status
    """

    def __init__(self):
        self.repo = None
        self.repo_path = ''
        self.repo_name = ''
        self.branch_name = ''
        self.unstaged_files = []
        self.staged_files = []
        self.has_staged_files = False

        # Callbacks — set by the View
        self.on_state_changed = None
        self.set_status = None

    def _notify_changed(self):
        if self.on_state_changed:
            self.on_state_changed()

    def _status(self, message, msg_type='info'):
        if self.set_status:
            self.set_status(message, msg_type)

    def open_repository(self, path):
        """Open a git repository.

        Returns:
            True if the repository was opened successfully.
        """
        repo, repo_path = gitops.open_repository(path)
        if repo:
            self.repo = repo
            self.repo_path = repo_path
            self.repo_name = gitops.get_repo_name(repo_path)
            self._update_branch_name()
            self.rescan()
            self._status('Opened repository: ' + path)
            return True
        else:
            self._status('Not a git repository: ' + path, 'warning')
            return False

    def rescan(self):
        """Rescan the repository for changes."""
        if self.repo is None:
            return

        unstaged, staged = gitops.get_status(self.repo)
        self.unstaged_files = unstaged
        self.staged_files = staged
        self.has_staged_files = len(staged) > 0

        self._update_branch_name()
        self._status('{} unstaged, {} staged changes'.format(
            len(unstaged), len(staged)))
        self._notify_changed()

    def close_repository(self):
        """Close the current repository."""
        self.repo = None
        self.repo_path = ''
        self.repo_name = ''
        self.branch_name = ''
        self.unstaged_files = []
        self.staged_files = []
        self.has_staged_files = False
        self._notify_changed()

    def _update_branch_name(self):
        """Update the branch name from the current repo."""
        if self.repo:
            self.branch_name = gitops.get_current_branch(self.repo) or ''
        else:
            self.branch_name = ''
