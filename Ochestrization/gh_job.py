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


# 오케스트레이터가 들어있는 현재 프로젝트의 Git root
PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


def prepare_repo(repo: str, repo_path: Path | str | None = None) -> Path:
    """
    repo_path가 있으면 해당 경로를 사용한다.
    없으면 현재 프로젝트의 Git root를 대상 repo로 사용한다.

    현재 프로젝트가 Git repo라면 clone하지 않고 그대로 재사용한다.
    """

    path = Path(repo_path).resolve() if repo_path else default_repo_path(repo)

    if (path / ".git").exists():
        logger.info(f"Using existing repo at {path}")
        return path

    # 명시적으로 전달된 경로가 존재하지만 Git repo가 아닌 경우
    if path.exists():
        raise ValueError(f"Not a git repository: {path}")

    logger.info(f"Cloning {repo} into {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["gh", "repo", "clone", repo, str(path)],
        check=True,
    )

    return path


def sync_main(repo_path: Path) -> None:
    """브랜치 생성 전에 main을 최신 상태로 동기화."""

    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", "main"],
        check=True,
    )

    logger.info(f"Checked out main branch in {repo_path}")

    subprocess.run(
        ["git", "-C", str(repo_path), "pull", "--ff-only", "origin", "main"],
        check=True,
    )

    logger.info(f"Pulled origin main in {repo_path}")


# ---------- 3. 브랜치 컷 ----------


def branch_cut(
    repo_path: Path,
    agent_name: str,
    model_name: str,
    issue_num: int,
) -> str:
    """
    Agent 실행마다 고유한 작업 브랜치를 생성한다.

    예:
    agent/cline-sonnet-issue-2-a81f32c1
    """

    run_id = uuid.uuid4().hex[:8]

    branch_name = (
        f"agent/{agent_name}-{model_name}"
        f"-issue-{issue_num}-{run_id}"
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

    logger.info(f"Created branch {branch_name}")

    return branch_name


# ---------- 4. (임시) 코드 작성 자리 ----------


def temp_code_change(repo_path: Path) -> None:
    """Phase 1 임시용: 더미 변경 → commit."""

    dummy_file = repo_path / "AGENT_TEST.md"
    dummy_file.write_text("agent pipeline smoke test\n")

    subprocess.run(
        ["git", "-C", str(repo_path), "add", "."],
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

    logger.info("Committed dummy change")


def push_branch(repo_path: Path, branch_name: str) -> None:
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

    logger.info(f"Pushed branch {branch_name}")


# ---------- 5. PR 생성 ----------


def create_pr(
    repo_path: Path,
    repo: str,
    title: str,
    body: str,
) -> str:
    """PR을 생성하고 URL을 반환."""

    result = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
            "--base",
            "main",
        ],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    )

    pr_url = result.stdout.strip()

    logger.info(f"Created PR: {pr_url}")

    return pr_url