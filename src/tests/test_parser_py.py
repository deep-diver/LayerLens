# test_parser_py.py

import pytest
import os
import shutil

from src.pipeline.parser_py import _is_github_url
from src.pipeline.parser_py import _clone_repo

def test_is_github_url():
    assert _is_github_url("https://github.com/user/repo") == True
    assert _is_github_url("https://github.com/user/repo.git") == True
    assert _is_github_url("github.com/user/repo") == False
    assert _is_github_url("user/repo") == False
    assert _is_github_url("http://github.com/user/repo") == False

def test_clone_repo():
    repo_path = _clone_repo("https://github.com/deep-diver/hiera")
    assert os.path.isdir(repo_path) == True
    assert os.path.exists(repo_path) == True
    shutil.rmtree(repo_path)