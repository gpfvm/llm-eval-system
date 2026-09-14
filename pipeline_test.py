import pytest
from pipeline import cleanup
import subprocess



# normal case test 
def test_cleanup_normal_main(repo_path):
    branch_name = "test-branch"
    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", "-b", branch_name],
        check=True,
    )

    cleanup(repo_path,branch_name)

    result = subprocess.run(
        ["git", "-C", str(repo_path), "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "main"

def test_cleanup_normal_delete_branch(repo_path):
    branch_name = "test-branch"
    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", "-b", branch_name],
        check=True,
    )

    cleanup(repo_path,branch_name)

    result = subprocess.run(
        ["git", "-C", str(repo_path), "branch", "--list", branch_name],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == ""

def test_cleanup_path_none(repo_path):
    branch_name = "test_branch"
    subprocess.run(
            ["git", "-C", str(repo_path), "checkout", "-b", branch_name],
            check=True,
        )
    
    cleanup(None,branch_name)
    
    result = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
    
    assert result.stdout.strip() == "test_branch"

def test_cleanup_branch_none(repo_path):
    branch_name = "test-branch"
    subprocess.run(
            ["git", "-C", str(repo_path), "checkout", "-b", branch_name],
            check=True,
        )
    
    cleanup(repo_path,None)
    
    result = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
    
    assert result.stdout.strip() == "main"