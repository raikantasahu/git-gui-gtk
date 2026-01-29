"""RemoteViewModel - manages remote operations (push, pull, fetch, CRUD).

All async operations (push, pull, fetch) are synchronous in this VM.
The View is responsible for running them in background threads and
dispatching results back to the main thread.
"""

import gitops


class RemoteViewModel:
    """ViewModel for remote operations."""

    def __init__(self, repo_vm):
        self._repo_vm = repo_vm

    def push(self, remote_name, branch_name=None, force=False, tags=False):
        """Push to a remote (synchronous).

        Returns:
            (success, message) tuple
        """
        return gitops.push(self._repo_vm.repo, remote_name, branch_name, force, tags)

    def pull(self, remote_name, branch_name=None, ff_only=False, rebase=False):
        """Pull from a remote (synchronous).

        Returns:
            (success, message) tuple
        """
        success, message = gitops.pull(
            self._repo_vm.repo, remote_name, branch_name, ff_only, rebase
        )
        if success:
            self._repo_vm.rescan()
        return success, message

    def fetch(self, remote_name):
        """Fetch from a remote (synchronous).

        Returns:
            (success, message) tuple
        """
        return gitops.fetch(self._repo_vm.repo, remote_name)

    def add_remote(self, name, url):
        """Add a new remote.

        Returns:
            (success, message) tuple
        """
        return gitops.add_remote(self._repo_vm.repo, name, url)

    def rename_remote(self, old_name, new_name):
        """Rename a remote.

        Returns:
            (success, message) tuple
        """
        return gitops.rename_remote(self._repo_vm.repo, old_name, new_name)

    def delete_remote(self, name):
        """Delete a remote.

        Returns:
            (success, message) tuple
        """
        return gitops.delete_remote(self._repo_vm.repo, name)
