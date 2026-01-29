"""BranchViewModel - manages branch operations (CRUD, merge, rebase, reset)."""

import gitops


class BranchViewModel:
    """ViewModel for branch operations."""

    def __init__(self, repo_vm):
        self._repo_vm = repo_vm

    def create_branch(self, name, base=None, checkout=False):
        """Create a new branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.create_branch(
            self._repo_vm.repo, name, start_point=base, checkout=checkout
        )
        self._repo_vm._status(message)
        if success:
            self._repo_vm._update_branch_name()
        return success, message

    def checkout_branch(self, name):
        """Checkout a branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.checkout_branch(self._repo_vm.repo, name)
        self._repo_vm._status(message)
        if success:
            self._repo_vm._update_branch_name()
            self._repo_vm.rescan()
        return success, message

    def rename_branch(self, old_name, new_name):
        """Rename a branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.rename_branch(self._repo_vm.repo, old_name, new_name)
        self._repo_vm._status(message)
        if success:
            self._repo_vm._update_branch_name()
        return success, message

    def delete_branch(self, name, force=False):
        """Delete a branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.delete_branch(self._repo_vm.repo, name, force=force)
        self._repo_vm._status(message)
        return success, message

    def reset_branch(self, target, mode='mixed'):
        """Reset the current branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.reset_branch(self._repo_vm.repo, target, mode=mode)
        self._repo_vm._status(message)
        if success:
            self._repo_vm.rescan()
        return success, message

    def merge_branch(self, branch, strategy='default'):
        """Merge a branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.merge_branch(
            self._repo_vm.repo, branch, strategy=strategy
        )
        self._repo_vm._status(message)
        if success:
            self._repo_vm._update_branch_name()
            self._repo_vm.rescan()
        return success, message

    def rebase_branch(self, onto):
        """Rebase the current branch.

        Returns:
            (success, message) tuple
        """
        success, message = gitops.rebase_branch(self._repo_vm.repo, onto)
        self._repo_vm._status(message)
        if success:
            self._repo_vm._update_branch_name()
            self._repo_vm.rescan()
        return success, message
