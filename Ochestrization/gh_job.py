import subprocess
import json
import logging
import uuid
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


# 현재 프로젝트의 Git repo 경로
#
# llm-eval-system/
# ├── main.py
# ├── pipeline.py
# └── Ochestrization/
#     └── gh_job.py
#
# 따라서 parent가 llm-eval-system
PROJECT_ROOT = Path(__file__).resolve().parent.parent


BASE_BRANCH = "mvp_dev"


# ---------- 1. 이슈 조회 ----------


def get_issues(repo: str, label: str = "AI:ready") -> list[int]:
    """label이 붙은 이슈 번호 목록을 가져온다."""

    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--label",
                label,
                "--json",
                "number",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        issues = json.loads(result.stdout)

        return [issue["number"] for issue in issues]

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list issues: {e.stderr}")
        return []


def get_issue_content(repo: str, issue_num: int) -> dict:
    """이슈 제목/본문을 가져온다."""

    result = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            str(issue_num),
            "--repo",
            repo,
            "--json",
            "title,body",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return json.loads(result.stdout)


# ---------- 2. repo 준비 ----------


def default_repo_path(repo: str) -> Path:
    """
    현재 오케스트레이터가 들어있는 프로젝트 자체를 대상 repo로 사용한다.
    """

    return PROJECT_ROOT


def prepare_repo(
    repo: str,
    repo_path: Path | str | None = None,
) -> Path:
    """
    로컬 repo가 없으면 clone하고,
    이미 존재하면 그대로 재사용한다.
    """

    path = (
        Path(repo_path).resolve()
        if repo_path
        else default_repo_path(repo)
    )

    # 이미 Git repo인 경우 그대로 사용
    if path.exists():

        if not (path / ".git").exists():
            raise ValueError(
                f"Not a git repository: {path}"
            )

        logger.info(
            f"Reusing existing repo at {path}"
        )

        return path

    # repo가 존재하지 않는 경우 clone
    logger.info(
        f"Cloning {repo} into {path}"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    subprocess.run(
        [
            "git",
            "clone",
            f"git@github.com:{repo}.git",
            str(path),
        ],
        check=True,
    )

    return path


# ---------- 3. Base branch 동기화 ----------


def sync_main(repo_path: Path) -> None:
    """
    Agent branch를 생성하기 전에
    mvp_dev를 최신 상태로 동기화한다.

    함수 이름은 기존 pipeline.py와의 호환성을 위해
    sync_main 그대로 유지한다.
    """

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "checkout",
            BASE_BRANCH,
        ],
        check=True,
    )

    logger.info(
        f"Checked out {BASE_BRANCH} branch"
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "pull",
            "--ff-only",
            "origin",
            BASE_BRANCH,
        ],
        check=True,
    )

    logger.info(
        f"Pulled origin/{BASE_BRANCH}"
    )


# ---------- 4. 브랜치 컷 ----------


def branch_cut(
    repo_path: Path,
    agent_name: str,
    model_name: str,
    issue_num: int,
) -> str:
    """
    Agent 작업용 고유 branch를 생성한다.

    예:
    cline_sonnet_issue2_1f1c67a0
    """

    run_id = uuid.uuid4().hex[:8]

    branch_name = (
        f"{agent_name}_"
        f"{model_name}_"
        f"issue{issue_num}_"
        f"{run_id}"
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "checkout",
            "-b",
            branch_name,
        ],
        check=True,
    )

    logger.info(
        f"Created branch {branch_name}"
    )

    return branch_name


# ---------- 5. (임시) 코드 작성 자리 ----------


def temp_code_change(repo_path: Path) -> None:
    """
    Phase 1 임시용:
    더미 변경 → commit.

    나중에 Cline 호출로 교체.
    """

    dummy_file = repo_path / "AGENT_TEST.md"

    dummy_file.write_text(
        "agent pipeline smoke test\n"
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "add",
            ".",
        ],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "commit",
            "-m",
            "chore: agent pipeline smoke test",
        ],
        check=True,
    )

    logger.info(
        "Committed dummy change"
    )


# ---------- 6. Branch Push ----------


def push_branch(
    repo_path: Path,
    branch_name: str,
) -> None:
    """Agent branch를 remote에 push한다."""

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "push",
            "-u",
            "origin",
            branch_name,
        ],
        check=True,
    )

    logger.info(
        f"Pushed branch {branch_name}"
    )


# ---------- 7. Pull Request 생성 ----------


def create_pr(
    repo_path: Path,
    repo: str,
    branch_name: str,
    title: str,
    body: str,
) -> str:
    """
    Agent branch -> mvp_dev PR 생성.
    """

    result = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--head",
            branch_name,
            "--base",
            BASE_BRANCH,
            "--title",
            title,
            "--body",
            body,
        ],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )

    # PR 생성 실패 시 실제 gh 에러를 출력
    if result.returncode != 0:

        logger.error(
            "Failed to create PR"
        )

        logger.error(
            f"stdout: {result.stdout}"
        )

        logger.error(
            f"stderr: {result.stderr}"
        )

        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )

    pr_url = result.stdout.strip()

    logger.info(
        f"Created PR: {pr_url}"
    )

    return pr_url

# commit changes
def commit_changes(repo_path: Path, issue_num: int) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    if not result.stdout.strip():
        raise RuntimeError(
            "No changes detected after agent execution."
        )

    subprocess.run(
        ["git", "-C", str(repo_path), "add", "-A"],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(repo_path),
            "commit",
            "-m",
            f"fix: implement issue #{issue_num}",
        ],
        check=True,
    )

    logger.info(
        f"Committed changes for issue #{issue_num}"
    )