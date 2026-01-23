"""Get diff operation."""

import os
from typing import Optional

from git import Repo, GitCommandError


def get_diff(
    repo: Optional[Repo],
    repo_path: Optional[str],
    path: str,
    staged: bool = False,
    context_lines: int = 3
) -> str:
    """Get diff for a specific file.

    Args:
        repo: Git repository object
        repo_path: Path to the repository
        path: File path relative to repo root
        staged: If True, show staged diff (index vs HEAD)
               If False, show unstaged diff (working tree vs index)
        context_lines: Number of context lines to show (default 3)

    Returns:
        Diff string or error message
    """
    if not repo:
        return ''

    try:
        context_arg = f'-U{context_lines}'
        if staged:
            # Staged: compare index to HEAD
            diff = repo.git.diff(context_arg, '--cached', '--', path)
        else:
            # Check if file is untracked
            if path in repo.untracked_files:
                # Show entire file content as new
                full_path = os.path.join(repo_path, path)
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
                diff = repo.git.diff(context_arg, '--', path)
        return diff
    except GitCommandError as e:
        return f'Error getting diff: {e}'
