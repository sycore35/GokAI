"""
Tests for extended JailedFileSystem features (create, edit, rename, search, traversal protection).
"""

import tempfile
from pathlib import Path
import pytest
from gokai.packages.tools.jailed_fs import JailedFileSystem
from gokai.packages.shared.exceptions import PathTraversalError


def test_fs_crud_and_edit():
    with tempfile.TemporaryDirectory() as tmp:
        fs = JailedFileSystem(Path(tmp))

        # Create
        f = fs.create_file("module/app.py", "def original(): pass\n")
        assert f.exists()
        assert fs.file_exists("module/app.py")

        # Read
        content = fs.read_file("module/app.py")
        assert "def original" in content

        # Edit (replace)
        edited = fs.edit_file("module/app.py", "def original", "def updated")
        assert edited is True
        assert "def updated" in fs.read_file("module/app.py")

        # Rename
        new_path = fs.rename_file("module/app.py", "module/renamed.py")
        assert new_path.exists()
        assert not fs.file_exists("module/app.py")
        assert fs.file_exists("module/renamed.py")

        # Search / Grep
        results = fs.search_files("def updated")
        assert len(results) >= 1
        assert results[0]["file"] == "module/renamed.py"

        # Delete
        assert fs.delete_file("module/renamed.py") is True
        assert not fs.file_exists("module/renamed.py")


def test_fs_path_traversal_prevention():
    with tempfile.TemporaryDirectory() as tmp:
        fs = JailedFileSystem(Path(tmp))

        with pytest.raises(PathTraversalError):
            fs.read_file("../../etc/passwd")

        with pytest.raises(PathTraversalError):
            fs.write_file("../../../malicious.txt", "attack")
