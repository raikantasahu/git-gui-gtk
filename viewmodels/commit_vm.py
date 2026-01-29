"""CommitViewModel - manages commit operations and amend mode."""

import gitops


class CommitViewModel:
    """ViewModel for commit and amend operations.

    Attributes:
        amend_mode: whether amend mode is active (bool)
    """

    def __init__(self, repo_vm):
        self._repo_vm = repo_vm
        self.amend_mode = False

    def commit(self, message, amend=False, sign_off=False):
        """Perform a commit.

        Returns:
            (success, result_message) tuple
        """
        if not message.strip() and not amend:
            return False, 'Please enter a commit message.'

        success, result_msg = gitops.commit(
            self._repo_vm.repo, message, amend=amend, sign_off=sign_off
        )
        if success:
            self._repo_vm._status(result_msg)
            self.amend_mode = False
            self._repo_vm.rescan()
        return success, result_msg

    def get_amend_data(self):
        """Get data needed to enter amend mode.

        Returns:
            (last_commit_message, merged_staged_files) tuple
        """
        last_msg = gitops.get_last_commit_message(self._repo_vm.repo)
        last_commit_files = gitops.get_last_commit_files(self._repo_vm.repo)
        _, currently_staged = gitops.get_status(self._repo_vm.repo)
        staged_paths = {f.path for f in last_commit_files}
        for f in currently_staged:
            if f.path not in staged_paths:
                last_commit_files.append(f)
        self.amend_mode = True
        return last_msg, last_commit_files

    def leave_amend_mode(self):
        """Leave amend mode and rescan."""
        self.amend_mode = False
        self._repo_vm.rescan()

    def toggle_amend(self):
        """Toggle amend mode.

        Returns:
            If entering amend mode: (True, last_message, files)
            If leaving amend mode: (False, None, None)
        """
        if not self.amend_mode:
            last_msg, files = self.get_amend_data()
            return True, last_msg, files
        else:
            self.leave_amend_mode()
            return False, None, None
