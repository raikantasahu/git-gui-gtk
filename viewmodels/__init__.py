"""ViewModels for Git GUI GTK.

ViewModels are plain Python classes with no GTK dependency.
They depend only on gitops (the model layer) and stdlib.
"""

from viewmodels.repository_vm import RepositoryViewModel
from viewmodels.file_list_vm import FileListViewModel
from viewmodels.diff_vm import DiffViewModel
from viewmodels.commit_vm import CommitViewModel
from viewmodels.remote_vm import RemoteViewModel
from viewmodels.branch_vm import BranchViewModel

__all__ = [
    'RepositoryViewModel',
    'FileListViewModel',
    'DiffViewModel',
    'CommitViewModel',
    'RemoteViewModel',
    'BranchViewModel',
]
