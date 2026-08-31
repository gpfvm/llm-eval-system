import pytest
from Ochestrization.gh_job import *
import subprocess
from unittest.mock import patch

REPO = "gpfvm/test_repo"
AGENT_NAME = "cline"
MODEL_NAME = "qwen_3"

# create mock origin repo at local temp folder
@pytest.fixture(scope="module")
def repo_path(tmp_path_factory):

    """
        1. create a mock github repo at local machine 
        2. make initial commit 
        3. mock clone 
        4. return mock repo path 
        
    """
    tmp = tmp_path_factory.mktemp("dryrun")

    origin = tmp / "origin"
    subprocess.run(["git", "init", str(origin)], check=True)
    (origin / "README.md").write_text("init\n")
    subprocess.run(["git", "-C", str(origin), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(origin),
         "-c", "user.email=test@test.com", "-c", "user.name=test",
         "commit", "-m", "init"],
        check=True,
    )

    work = tmp / "work"
    subprocess.run(["git", "clone", str(origin), str(work)], check=True)

    path = work
    assert path.exists(), "returned not existing path"
    assert (path / ".git").exists(), "returned not git existing path"
    return path


# test sync-main 
def test_sync_main(repo_path):
    sync_main(repo_path)

    current_branch = subprocess.run(["git", "-C", str(repo_path),"branch", "--show-current"], capture_output=True, text=True, check=True)

    assert current_branch.stdout.strip() == "main", "current branch is not main"

#mocking subprocess.run contains "gh" command 
@patch("Ochestrization.gh_job.subprocess.run")
def test_get_issues(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
    args=[], returncode=0,
    stdout='[{"number": 1}, {"number": 2}]',
    stderr="",
    )
    issues = get_issues(REPO)

    assert len(issues) > 0 , "issues is empty list"
    assert all(isinstance(n,int) for n in issues) , "no int type"  
    assert isinstance(issues,list)

@patch("Ochestrization.gh_job.subprocess.run")
def test_get_issue_content(mock_run):
    mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0,
        stdout='{"title": "issue title", "body": "issue body"}',
        stderr="",
    )
    content = get_issue_content(REPO,1)

    assert "title" in content, "contents dose not have key 'title'"
    assert content["title"], "title is empty string"

    assert "body" in content, "contents dose not have key 'body'"
    assert content["body"], "body is empty string"


# test get_issue_contents_failure case 
@patch("Ochestrization.gh_job.subprocess.run")
def test_get_issue_content_invalid_issue(mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["gh", "issue", "view"], stderr="issue not found"
    )
    with pytest.raises(RuntimeError):
        get_issue_content(REPO, 99999)

#teset_branch_cut
def test_branch_cut(repo_path):
    """
    branch_cut returns branch name in str type
    validate name convention of branch 
    validate branch is checkedout  
    """
    branch_name = branch_cut(repo_path,AGENT_NAME,MODEL_NAME,1)
    current_branch = subprocess.run(["git", "-C", str(repo_path),"branch", "--show-current"], capture_output=True, text=True, check=True)

    assert branch_name == f"{AGENT_NAME}_{MODEL_NAME}_issue1"
    assert current_branch.stdout.strip() == branch_name
    

#test_get_commit_sha and commmit_changes 
def test_commit_and_diff(repo_path):
    filename = "AGENT_TEST.md"
    dummy_file = repo_path / filename
    dummy_file.write_text("agent pipeline smoke test\n")
    sha = commit_changes(repo_path,"#1: AGENT_TEST")

    assert len(sha) == 40, "SHA must be 40 digit+alphabet"
    assert all(c in "0123456789abcdef" for c in sha), "SHA is not hex format"

    diff = get_commit_diff(repo_path,sha)

    assert filename in diff, "file should be shown in diff"

#push_branch test 
@patch("Ochestrization.gh_job.subprocess.run")
def test_push_branch(mock_run,repo_path):
        mock_run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0,)
        push_branch(repo_path,"mock_branch")

        called_args= mock_run.call_args[0][0]
        assert "push" in called_args, "push command is not included"
        assert "mock_branch" in called_args, "branch name is incorrect"

@patch("Ochestrization.gh_job.subprocess.run")
def test_create_pr(mock_run,repo_path):
    mock_run.return_value= subprocess.CompletedProcess(
        args=[], returncode=0,
        stdout="https://github.com/mock_repo/pull/1\n",
        stderr="",
    )
    mock_result = create_pr(repo_path, "mock_repo", "title", "body")

    mock_url = mock_result
    assert mock_url == "https://github.com/mock_repo/pull/1", "pr URL is not correct."

# Create PR failure case
@patch("Ochestrization.gh_job.subprocess.run")
def test_create_pr_failure(mock_run,repo_path):
    mock_run.return_value= subprocess.CompletedProcess(
        args=[], returncode=1,
        stdout="",
        stderr="PR already exists",
    )
    with pytest.raises(RuntimeError) as exc_info:
        create_pr(repo_path, "mock_repo", "title", "body")
    assert "PR already exists" in str(exc_info.value)