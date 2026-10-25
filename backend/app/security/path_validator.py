"""
Path Traversal and Safe Filename Validation Utility.
Prevents directory traversal, absolute path escapes, null-byte injection,
and dangerous executable extensions in file and repository operations.
"""
from __future__ import annotations

import os
import re
from typing import Optional


# Prohibited extensions that must never be created or targeted by automated patch workflows
DISALLOWED_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".ps1", ".vbs",
    ".sh", ".bash", ".bin", ".dll", ".so", ".dylib",
    ".jar", ".war", ".ear",
}

# Regex for safe relative file path: only alphanumeric, underscores, hyphens, dots, and forward slashes
SAFE_PATH_REGEX = re.compile(r"^[a-zA-Z0-9_\-\./]+$")


def validate_safe_relative_path(path: str, max_length: int = 255) -> str:
    """
    Validates that a path is a safe, normalized relative file path within a repository workspace.
    Raises ValueError if path traversal, absolute path, null-bytes, or disallowed patterns are detected.
    """
    if not path or not isinstance(path, str):
        raise ValueError("File path cannot be empty.")

    cleaned = path.strip()
    if not cleaned:
        raise ValueError("File path cannot be empty whitespace.")

    if len(cleaned) > max_length:
        raise ValueError(f"File path exceeds maximum allowed length of {max_length} characters.")

    # Check for null bytes
    if "\x00" in cleaned or "%00" in cleaned:
        raise ValueError("Null-byte injection detected in file path.")

    # Check for directory traversal sequences
    if ".." in cleaned or "/." in cleaned or "\\." in cleaned:
        raise ValueError("Directory traversal sequence ('..') detected in file path.")

    # Check for absolute path (Unix or Windows drive letter)
    if cleaned.startswith(("/", "\\")) or re.match(r"^[a-zA-Z]:", cleaned):
        raise ValueError("Absolute paths are strictly prohibited; target file must be relative to repository root.")

    # Normalize forward slashes
    normalized = cleaned.replace("\\", "/")

    # Check allowed characters
    if not SAFE_PATH_REGEX.match(normalized):
        raise ValueError("File path contains disallowed or dangerous characters.")

    # Check extension
    _, ext = os.path.splitext(normalized)
    if ext.lower() in DISALLOWED_EXTENSIONS:
        raise ValueError(f"Targeting executable or binary extension '{ext}' is prohibited.")

    return normalized


def validate_safe_branch_name(branch_name: Optional[str]) -> Optional[str]:
    """
    Validates that a Git branch name complies with safe Git ref naming rules and contains no control characters.
    """
    if not branch_name:
        return None

    cleaned = branch_name.strip()
    if not cleaned:
        return None

    if len(cleaned) > 120:
        raise ValueError("Branch name exceeds maximum length of 120 characters.")

    # Git ref safety checks
    if any(c in cleaned for c in [" ", "~", "^", ":", "?", "*", "[", "\\", "\x00", "\n", "\r", "\t"]):
        raise ValueError("Branch name contains illegal Git reference characters.")

    if ".." in cleaned or cleaned.startswith((".", "/")) or cleaned.endswith((".", "/", ".lock")):
        raise ValueError("Invalid Git branch name format.")

    if not re.match(r"^[a-zA-Z0-9_\-\./]+$", cleaned):
        raise ValueError("Branch name contains invalid characters.")

    return cleaned
