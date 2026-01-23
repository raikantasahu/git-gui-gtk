"""Revert single line operation."""

import re
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


def _parse_hunk_header(header: str) -> tuple[int, int, int, int]:
    """Parse a hunk header line.

    Args:
        header: The @@ line

    Returns:
        Tuple of (old_start, old_count, new_start, new_count)
    """
    match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', header)
    if match:
        old_start = int(match.group(1))
        old_count = int(match.group(2)) if match.group(2) else 1
        new_start = int(match.group(3))
        new_count = int(match.group(4)) if match.group(4) else 1
        return old_start, old_count, new_start, new_count
    return 1, 0, 1, 0


def _create_single_line_hunk(hunk_lines: list[str], line_in_hunk: int) -> list[str]:
    """Create a hunk that only reverts a single line.

    Args:
        hunk_lines: The original hunk lines (including @@ header)
        line_in_hunk: Index of the line to revert within the hunk (0 = @@ header)

    Returns:
        Modified hunk lines with only the selected line as a change
    """
    if line_in_hunk <= 0 or line_in_hunk >= len(hunk_lines):
        return hunk_lines  # Return original if invalid

    target_line = hunk_lines[line_in_hunk]

    # Check if target line is a change line
    if not target_line or target_line[0] not in ['+', '-']:
        return []  # Can't revert a context line

    is_addition = target_line[0] == '+'
    old_start, old_count, new_start, new_count = _parse_hunk_header(hunk_lines[0])

    # Build new hunk: convert other changes to context, keep target line
    new_hunk_body = []
    new_old_count = 0
    new_new_count = 0

    for i, line in enumerate(hunk_lines[1:], start=1):
        if not line:
            # Empty line - treat as context
            new_hunk_body.append(' ')
            new_old_count += 1
            new_new_count += 1
            continue

        line_type = line[0] if line else ' '
        line_content = line[1:] if line else ''

        if i == line_in_hunk:
            # This is the line we want to revert
            new_hunk_body.append(line)
            if is_addition:
                new_new_count += 1
            else:
                new_old_count += 1
        elif line_type == '+':
            # Convert other additions to context (they exist in working tree)
            # Skip them - they stay as working tree changes
            pass
        elif line_type == '-':
            # Convert other deletions to context (keep the original line)
            new_hunk_body.append(' ' + line_content)
            new_old_count += 1
            new_new_count += 1
        else:
            # Context line - keep as is
            new_hunk_body.append(line)
            new_old_count += 1
            new_new_count += 1

    # Create new header
    new_header = f'@@ -{old_start},{new_old_count} +{new_start},{new_new_count} @@'

    return [new_header] + new_hunk_body


def revert_line(
    repo: Optional[Repo],
    file_path: str,
    diff_line: int
) -> tuple[bool, str]:
    """Revert a specific line from a file (discard change in working tree).

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
            return False, 'Could not find hunk at cursor position'

        hunk_start, hunk_end, hunk_lines = hunks[hunk_idx]

        # Calculate line position within the hunk
        line_in_hunk = diff_line - hunk_start

        # Check if the line is a change line
        if line_in_hunk <= 0 or line_in_hunk >= len(hunk_lines):
            return False, 'Cursor is not on a change line'

        target_line = hunk_lines[line_in_hunk]
        if not target_line or target_line[0] not in ['+', '-']:
            return False, 'Selected line is not an addition or deletion'

        # Create a hunk with just this line
        modified_hunk = _create_single_line_hunk(hunk_lines, line_in_hunk)
        if not modified_hunk:
            return False, 'Could not create patch for selected line'

        # Build the patch
        patch_lines = header_lines + modified_hunk

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
            line_type = 'addition' if target_line[0] == '+' else 'deletion'
            return True, f'Reverted {line_type} line from {file_path}'
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return False, f'Failed to revert line: {error}'

    except Exception as e:
        return False, f'Error reverting line: {e}'
