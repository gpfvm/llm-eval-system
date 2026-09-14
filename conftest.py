import pytest
import subprocess

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