"""Unstage lines operation (single or multi-line selection)."""

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


def _create_lines_hunk(hunk_lines: list[str], target_lines_in_hunk: set[int]) -> list[str]:
    """Create a hunk that only unstages the specified lines.

    Args:
        hunk_lines: The original hunk lines (including @@ header)
        target_lines_in_hunk: Set of indices within hunk_lines to unstage
                              (0 = @@ header, so valid targets start at 1)

    Returns:
        Modified hunk lines with only the selected lines as changes
    """
    if not target_lines_in_hunk:
        return []

    old_start, old_count, new_start, new_count = _parse_hunk_header(hunk_lines[0])

    # Build new hunk: convert other changes to context, keep target lines
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

        if i in target_lines_in_hunk:
            # This is a line we want to unstage - keep the change marker
            new_hunk_body.append(line)
            if line_type == '+':
                new_new_count += 1
            else:
                new_old_count += 1
        elif line_type == '+':
            # Other additions exist in the index and must appear as
            # context so git apply --cached --reverse can match.
            new_hunk_body.append(' ' + line_content)
            new_old_count += 1
            new_new_count += 1
        elif line_type == '-':
            # Other deletions don't exist in the index, so they
            # can't appear as context. Skip them.
            pass
        else:
            # Context line - keep as is
            new_hunk_body.append(line)
            new_old_count += 1
            new_new_count += 1

    # Create new header
    new_header = f'@@ -{old_start},{new_old_count} +{new_start},{new_new_count} @@'

    return [new_header] + new_hunk_body


def unstage_lines(
    repo: Optional[Repo],
    file_path: str,
    start_line: int,
    end_line: int,
    context_lines: int = 3
) -> tuple[bool, str]:
    """Unstage specific lines from a file.

    When start_line == end_line, this unstages a single line (original behaviour).
    When they differ, all change lines in the range are unstaged.

    Args:
        repo: Git repository object
        file_path: Path to the file
        start_line: First diff line number in the selection (0-indexed)
        end_line: Last diff line number in the selection (0-indexed)
        context_lines: Number of context lines (must match the displayed diff)

    Returns:
        Tuple of (success, message)
    """
    if not repo:
        return False, 'No repository open'

    try:
        # Get the staged diff for this file, using the same context
        # as the displayed diff so line numbers match.
        diff_text = repo.git.diff(f'-U{context_lines}', '--cached', '--', file_path)
        if not diff_text:
            return False, 'No staged changes to unstage'

        # Parse the diff into hunks
        header_lines, hunks = _parse_diff_into_hunks(diff_text)

        if not hunks:
            return False, 'No hunks found in diff'

        # Collect change lines per hunk within the selected range
        all_modified_hunk_lines = []
        total_unstaged = 0

        for hunk_idx, (hunk_start, hunk_end, hunk_lines) in enumerate(hunks):
            target_indices = set()
            for i, line in enumerate(hunk_lines[1:], start=1):
                abs_line = hunk_start + i
                if start_line <= abs_line <= end_line and line and line[0] in ('+', '-'):
                    target_indices.add(i)

            if target_indices:
                modified = _create_lines_hunk(hunk_lines, target_indices)
                if modified:
                    all_modified_hunk_lines.extend(modified)
                    total_unstaged += len(target_indices)

        if not all_modified_hunk_lines:
            return False, 'No change lines found in the selected range'

        # Build the patch
        patch_lines = header_lines + all_modified_hunk_lines

        # Ensure patch ends with newline
        patch = '\n'.join(patch_lines)
        if not patch.endswith('\n'):
            patch += '\n'

        # Apply the patch in reverse to the index to unstage
        result = subprocess.run(
            ['git', 'apply', '--cached', '--reverse', '--verbose'],
            input=patch,
            capture_output=True,
            text=True,
            cwd=repo.working_dir
        )

        if result.returncode == 0:
            if total_unstaged == 1:
                return True, f'Unstaged 1 line from {file_path}'
            return True, f'Unstaged {total_unstaged} lines from {file_path}'
        else:
            error = result.stderr.strip() or result.stdout.strip()
            return False, f'Failed to unstage lines: {error}'

    except Exception as e:
        return False, f'Error unstaging lines: {e}'
