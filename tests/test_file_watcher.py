import pytest
import tempfile
import os
from unittest.mock import patch
from src.file_watcher import FileWatcher

def test_file_watcher_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = FileWatcher(root_dir=tmpdir)
        assert watcher.root_dir == tmpdir
