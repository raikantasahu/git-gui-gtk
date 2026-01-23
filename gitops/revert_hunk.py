"""Revert hunk operation."""

import subprocess
from typing import Optional

from git import Repo


def _parse_diff_into_hunks(diff_text: str) -> tuple[list[str], list[tuple[int, int, list[str]]]]:
    """Parse a diff into header and hunks.

    Args:
        diff_text: The full diff text

    Returns:
        Tuple of (header_lines, hunks) where hunks is a list of
        (start_line, end_line, hunk_lines) tuples.
        start_line and end_line are line numbers in the diff text (0-indexed).
    """
    lines = diff_text.split('\n')
    header_lines = []
    hunks = []

    i = 0
    # Collect header lines (everything before first @@)
    while i < len(lines) and not lines[i].startswith('@@'):
        header_lines.append(lines[i])
        i += 1

    # Parse hunks
    while i < len(lines):
        if lines[i].startswith('@@'):
            hunk_start = i
            hunk_lines = [lines[i]]
            i += 1

            # Collect lines until next @@ or end
            while i < len(lines) and not lines[i].startswith('@@'):
                hunk_lines.append(lines[i])
                i += 1

            hunk_end = i - 1
            hunks.append((hunk_start, hunk_end, hunk_lines))
        else:
            i += 1

    return header_lines, hunks


def _find_hunk_at_line(hunks: list[tuple[int, int, list[str]]], line: int) -> int:
    """Find the index of the hunk containing the given line.

    Args:
        hunks: List of (start_line, end_line, hunk_lines) tuples
        line: Line number in the diff (0-indexed)

    Returns:
        Index of the hunk, or -1 if not found
    """
    for idx, (start, end, _) in enumerate(hunks):
        if start <= line <= end:
            return idx
    return -1


def revert_hunk(
    repo: Optional[Repo],
    file_path: str,
    diff_line: int
) -> tuple[bool, str]:
    """Revert a specific hunk from a file (discard changes in working tree).

    Args:
        repo: Git repository object
        file_path: Path to the file
        diff_line: Line number in the diff where the cursor is (0-indexed)

    Returns:
        Tuple of (success, message)
    """
    if not repo:
        return False, 'No repository open'

    try:
        # Get the unstaged diff for this file
        diff_text = repo.git.diff('--', file_path)
        if not diff_text:
            return False, 'No unstaged changes to revert'

        # Parse the diff into hunks
        header_lines, hunks = _parse_diff_into_hunks(diff_text)

        if not hunks:
            return False, 'No hunks found in diff'

        # Find which hunk contains the cursor line
        hunk_idx = _find_hunk_at_line(hunks, diff_line)
        if hunk_idx == -1:
            # If cursor is in header, revert first hunk
            if diff_line < len(header_lines):
                hunk_idx = 0
            else:
                return False, 'Could not find hunk at cursor position'

        # Build the patch with just this hunk
        _, _, hunk_lines = hunks[hunk_idx]
        patch_lines = header_lines + hunk_lines

        # Ensure patch ends with newline
        patch = '\n'.join(patch_lines)
        if not patch.endswith('\n'):
            patch += '\n'

        # Apply the patch in reverse to the working tree
        result = subprocess.run(
            ['git', 'apply', '--reverse', '--verbose'],
            input=patch,
            capture_output=True,
            text=True,
            cwd=repo.working_dir
        )

        if result.returncode == 0:
            return True, f'Reverted hunk {hunk_idx + 1} of {len(hunks)} from {file_path}'
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return False, f'Failed to revert hunk: {error}'

    except Exception as e:
        return False, f'Error reverting hunk: {e}'
