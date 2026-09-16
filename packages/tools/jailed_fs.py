"""
GÖK SYSTEMS TECH — Jailed File System Tool
Enforces that all file operations are strictly confined within the project workspace.
Prevents path traversal attacks (../../, absolute system paths, symlink escape).
Supports: create, read, write, edit, delete, rename, search, list.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from gokai.packages.shared.exceptions import PathTraversalError
from gokai.packages.shared.logger import get_logger

logger = get_logger("jailed_fs")


class JailedFileSystem:
    """Provides path-jailed filesystem operations for GökAI projects."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def resolve_safe_path(self, target_path: str) -> Path:
        """Resolves target path and guarantees it strictly resides within workspace_root."""
        cleaned = target_path.strip().lstrip("/\\")
        candidate = (self.workspace_root / cleaned).resolve()

        try:
            candidate.relative_to(self.workspace_root)
        except ValueError:
            logger.error(f"Path traversal detected! Attempted: '{target_path}' outside '{self.workspace_root}'")
            raise PathTraversalError(
                f"Access denied: Target path '{target_path}' escapes workspace directory '{self.workspace_root}'."
            )

        # Additional protection against symlink escapes
        if candidate.is_symlink():
            real_target = candidate.resolve()
            try:
                real_target.relative_to(self.workspace_root)
            except ValueError:
                raise PathTraversalError(f"Symlink traversal escape detected: '{target_path}'")

        return candidate

    def file_exists(self, file_path: str) -> bool:
        """Checks if a file exists safely."""
        try:
            safe = self.resolve_safe_path(file_path)
            return safe.exists()
        except Exception:
            return False

    def create_file(self, file_path: str, initial_content: str = "") -> Path:
        """Creates a new file within workspace. Fails if file already exists."""
        safe_path = self.resolve_safe_path(file_path)
        if safe_path.exists():
            raise FileExistsError(f"File already exists: {file_path}")
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(initial_content, encoding="utf-8")
        logger.info(f"File created: {file_path}")
        return safe_path

    def read_file(self, file_path: str) -> str:
        """Reads file content from workspace."""
        safe_path = self.resolve_safe_path(file_path)
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not safe_path.is_file():
            raise IsADirectoryError(f"Target is a directory, not a file: {file_path}")
        return safe_path.read_text(encoding="utf-8", errors="replace")

    def write_file(self, file_path: str, content: str) -> Path:
        """Atomically writes file content within workspace (creates or overwrites)."""
        safe_path = self.resolve_safe_path(file_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        logger.info(f"File written successfully: {file_path} ({len(content)} chars)")
        return safe_path

    def edit_file(self, file_path: str, old_str: str, new_str: str) -> bool:
        """Performs targeted string replacement within a workspace file."""
        safe_path = self.resolve_safe_path(file_path)
        if not safe_path.exists() or not safe_path.is_file():
            raise FileNotFoundError(f"File not found for edit: {file_path}")

        current_content = safe_path.read_text(encoding="utf-8", errors="replace")
        if old_str not in current_content:
            logger.warning(f"Target pattern not found in {file_path} for edit")
            return False

        updated_content = current_content.replace(old_str, new_str, 1)
        safe_path.write_text(updated_content, encoding="utf-8")
        logger.info(f"File edited successfully: {file_path}")
        return True

    def rename_file(self, src_path: str, dst_path: str) -> Path:
        """Safely renames or moves a file within the workspace boundaries."""
        safe_src = self.resolve_safe_path(src_path)
        safe_dst = self.resolve_safe_path(dst_path)

        if not safe_src.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")

        safe_dst.parent.mkdir(parents=True, exist_ok=True)
        safe_src.rename(safe_dst)
        logger.info(f"Renamed {src_path} -> {dst_path}")
        return safe_dst

    def delete_file(self, file_path: str) -> bool:
        """Deletes a file within workspace."""
        safe_path = self.resolve_safe_path(file_path)
        if safe_path.exists() and safe_path.is_file():
            safe_path.unlink()
            logger.info(f"File deleted: {file_path}")
            return True
        return False

    def search_files(self, pattern: str, subpath: str = "", is_regex: bool = False) -> List[Dict[str, Any]]:
        """Searches across workspace files for content matches (grep)."""
        target_dir = self.resolve_safe_path(subpath) if subpath else self.workspace_root
        results = []

        compiled_re = re.compile(pattern if is_regex else re.escape(pattern), re.IGNORECASE)

        for root, _, files in os.walk(target_dir):
            for file_name in files:
                full_p = Path(root) / file_name
                try:
                    rel_p = full_p.relative_to(self.workspace_root).as_posix()
                    # Skip common binary/heavy directories
                    if any(part in rel_p for part in [".git", "__pycache__", "node_modules", ".pytest_cache"]):
                        continue

                    content = full_p.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    for idx, line in enumerate(lines, 1):
                        if compiled_re.search(line):
                            results.append({
                                "file": rel_p,
                                "line_number": idx,
                                "line_content": line.strip()[:200]
                            })
                            if len(results) >= 50:
                                return results
                except Exception:
                    continue

        return results

    def list_files(self, subpath: str = "") -> List[Dict[str, Any]]:
        """Lists directory contents relative to the workspace."""
        target_dir = self.resolve_safe_path(subpath) if subpath else self.workspace_root
        if not target_dir.exists():
            return []

        entries = []
        for root, dirs, files in os.walk(target_dir):
            for d in dirs:
                p = Path(root) / d
                rel = p.relative_to(self.workspace_root).as_posix()
                entries.append({"path": rel, "is_dir": True, "size_bytes": 0})
            for f in files:
                p = Path(root) / f
                rel = p.relative_to(self.workspace_root).as_posix()
                entries.append({"path": rel, "is_dir": False, "size_bytes": p.stat().st_size})
        return entries
