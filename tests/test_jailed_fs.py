"""
Tests for JailedFileSystem and Path Traversal Protection.
"""

import pytest
import tempfile
from pathlib import Path
from gokai.packages.tools.jailed_fs import JailedFileSystem
from gokai.packages.shared.exceptions import PathTraversalError


def test_jailed_fs_read_write_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = JailedFileSystem(Path(tmpdir))

        # Write file
        written_path = fs.write_file("test.py", "print('hello gokai')")
        assert written_path.exists()

        # Read file
        content = fs.read_file("test.py")
        assert content == "print('hello gokai')"

        # List files
        files = fs.list_files()
        assert len(files) >= 1
        assert files[0]["path"] == "test.py"

        # Delete file
        assert fs.delete_file("test.py") is True
        assert not written_path.exists()


def test_jailed_fs_path_traversal_blocked():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = JailedFileSystem(Path(tmpdir))

        # Attempt path traversal outside workspace
        with pytest.raises(PathTraversalError):
            fs.resolve_safe_path("../../windows/system32/cmd.exe")

        with pytest.raises(PathTraversalError):
            fs.write_file("../malicious.txt", "escaped content")
