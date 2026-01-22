"""Utility functions for Git GUI GTK."""

import os
import re
from typing import Optional


def find_git_root(path: str) -> Optional[str]:
    """Find the root of a git repository.

    Args:
        path: Starting path to search from

    Returns:
        Path to git root, or None if not in a git repo
    """
    current = os.path.abspath(path)
    while current != '/':
        if os.path.isdir(os.path.join(current, '.git')):
            return current
        current = os.path.dirname(current)
    return None


def get_file_icon_name(filename: str) -> str:
    """Get an appropriate icon name for a file.

    Args:
        filename: The filename to get an icon for

    Returns:
        GTK icon name
    """
    ext = os.path.splitext(filename)[1].lower()

    icon_map = {
        '.py': 'text-x-python',
        '.js': 'text-x-javascript',
        '.ts': 'text-x-javascript',
        '.html': 'text-html',
        '.css': 'text-css',
        '.json': 'text-x-generic',
        '.xml': 'text-xml',
        '.md': 'text-x-generic',
        '.txt': 'text-x-generic',
        '.sh': 'text-x-script',
        '.c': 'text-x-c',
        '.cpp': 'text-x-c++',
        '.h': 'text-x-c',
        '.hpp': 'text-x-c++',
        '.java': 'text-x-java',
        '.rs': 'text-x-generic',
        '.go': 'text-x-generic',
        '.rb': 'text-x-ruby',
        '.php': 'text-x-php',
        '.sql': 'text-x-sql',
        '.yml': 'text-x-generic',
        '.yaml': 'text-x-generic',
        '.toml': 'text-x-generic',
        '.ini': 'text-x-generic',
        '.cfg': 'text-x-generic',
        '.conf': 'text-x-generic',
    }

    return icon_map.get(ext, 'text-x-generic')


def format_file_size(size: int) -> str:
    """Format file size in human-readable format.

    Args:
        size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} PB'


def truncate_path(path: str, max_length: int = 50) -> str:
    """Truncate a path to fit within max_length.

    Args:
        path: Path to truncate
        max_length: Maximum length

    Returns:
        Truncated path with ellipsis if needed
    """
    if len(path) <= max_length:
        return path

    parts = path.split(os.sep)
    if len(parts) <= 2:
        return '...' + path[-(max_length - 3):]

    # Keep first and last parts, truncate middle
    result = parts[0] + os.sep + '...' + os.sep + parts[-1]
    if len(result) > max_length:
        return '...' + path[-(max_length - 3):]
    return result


def is_valid_branch_name(name: str) -> bool:
    """Check if a branch name is valid according to git rules.

    Args:
        name: Branch name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False

    # Cannot start with a dot
    if name.startswith('.'):
        return False

    # Cannot end with a slash
    if name.endswith('/'):
        return False

    # Cannot end with .lock
    if name.endswith('.lock'):
        return False

    # Cannot contain these patterns/characters
    invalid_patterns = [
        r'\.\.',      # double dots
        r'@\{',       # @{
        r'[\s~^:?*\[\]\\]',  # space, ~, ^, :, ?, *, [, ], \
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, name):
            return False

    # Cannot have consecutive slashes
    if '//' in name:
        return False

    # Cannot have a component starting with a dot (e.g., foo/.bar)
    if '/.' in name:
        return False

    return True


def is_binary_file(filepath: str) -> bool:
    """Check if a file is binary.

    Args:
        filepath: Path to the file

    Returns:
        True if the file appears to be binary
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)
            if b'\x00' in chunk:
                return True
            # Check for high ratio of non-text bytes
            text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
            non_text = sum(1 for b in chunk if b not in text_chars)
            return non_text / len(chunk) > 0.3 if chunk else False
    except Exception:
        return False
