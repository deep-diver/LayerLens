import os
import git

def _clone_repo(repo_url: str):
    repo_name = repo_url.split("/")[-1]
    repo_name = repo_name.split(".")[0]
    repo_path = os.path.join(os.getcwd(), repo_name)
    git.Repo.clone_from(repo_url, repo_path)
    return repo_path

def _is_github_url(path: str):
    return path.startswith("https://github.com/")

def parse_repo(path: str):
    # 1. determine if the path is a local directory or a GitHub URL
    if _is_github_url(path):
        # 2. clone the repository
        path = _clone_repo(path)

    # raise error if the path is not a valid directory
    if not os.path.isdir(path):
        raise ValueError(f"The path {path} is not a valid directory")

    return path