import subprocess
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 오케스트레이터 스크립트 기준 경로. 대상 repo들은 이 스크립트의 "부모 폴더"에
# 형제 디렉토리로 clone된다고 가정 (Mac/Windows 무관, 하드코딩 경로 불필요)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PARENT_DIR = PROJECT_ROOT.parent


# ---------- 1. 이슈 조회 ----------

def get_issues(repo: str, label: str = "AI:ready") -> list[int]:
    """label이 붙은 이슈 번호 목록을 가져온다."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--label", label, "--json", "number"],
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
    try:
        """이슈 제목/본문을 가져온다. repo를 안 넘기면 현재 디렉토리 기준으로 동작해 예측 불가능해지므로 필수."""
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_num), "--repo", repo, "--json", "title,body"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{issue_num} not found : {e.stderr}") from e


# ---------- 2. repo 준비 ----------

def default_repo_path(repo: str) -> Path:
    """ 오케스트레이터 부모 폴더/llm-eval-system 로 자동 계산."""
    repo_name = repo.split("/")[-1]
    return PARENT_DIR / repo_name


def prepare_repo(repo: str, repo_path: Path | str | None = None) -> Path:
    """로컬(부모 폴더)에 repo가 없으면 clone, 있으면 그대로 재사용.

    repo_path를 명시하면 그 경로를 우선 사용, 생략하면 default_repo_path로 자동 계산.
    gh CLI로 clone하므로 SSH 키 설정과 무관하게 gh auth login 인증을 그대로 재사용.
    """
    path = Path(repo_path).resolve() if repo_path else default_repo_path(repo)

    if path.exists():
        if not (path / ".git").exists():
            raise ValueError(f"Not a git repository: {path}")
        logger.info(f"Reusing existing repo at {path}")
        return path

    logger.info(f"Cloning {repo} into {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gh", "repo", "clone", repo, str(path)], check=True)
    return path


def sync_main(repo_path: Path) -> None:
    """브랜치 컷 직전 main을 최신화."""
    subprocess.run(["git", "-C", str(repo_path), "checkout", "main"], check=True)
    logger.info(f"Checked out main branch in {repo_path}")
    subprocess.run(["git", "-C", str(repo_path), "pull", "origin", "main"], check=True)
    logger.info(f"Pulled origin main in {repo_path}")


# ---------- 3. 브랜치 컷 ----------

def branch_cut(repo_path: Path, agent_name: str, model_name: str, issue_num: int) -> str:
    """<Agent>_<Model>_issue# 브랜치를 만들고 이름을 반환."""
    branch_name = f"{agent_name}_{model_name}_issue{issue_num}"
    subprocess.run(
        ["git", "-C", str(repo_path), "checkout", "-b", branch_name],
        check=True,
    )
    logger.info(f"Created branch {branch_name}")
    return branch_name


# ---------- 4. (임시) 코드 작성 자리 ----------

def temp_code_change(repo_path: Path) -> None:
    """Phase 1 임시용: 더미 변경 → commit. 나중에 Cline 호출로 교체될 자리."""
    dummy_file = repo_path / "AGENT_TEST.md"
    dummy_file.write_text("agent pipeline smoke test\n")

    subprocess.run(["git", "-C", str(repo_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-m", "chore: agent pipeline smoke test"],
        check=True,
    )
    logger.info("Committed dummy change")


# ---------- 5. 수정사항 Git Commit ----------
"""
수정사항 git hash 확보 
"""
def get_commit_sha(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def commit_changes(repo_path: Path, message: str) -> str:
    subprocess.run(
        ["git", "add", "."],
        cwd=repo_path,
        check=True,
    )

    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_path,
        check=True,
    )

    return get_commit_sha(repo_path)

# ---------- 6. commit diff / changed files 수집 ----------

def get_commit_diff(repo_path: Path, commit_sha: str) -> str:
    result = subprocess.run(
        ["git", "show", "--format=", commit_sha],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def push_branch(repo_path: Path, branch_name: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo_path), "push", "-u", "origin", branch_name],
        check=True,
    )
    logger.info(f"Pushed branch {branch_name}")


# ---------- 7. PR 생성 ----------

def create_pr(repo_path: Path, repo: str, title: str, body: str) -> str:
    result = subprocess.run(
        ["gh", "pr", "create", "--repo", repo, "--title", title, "--body", body, "--base", "main"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"gh pr create failed: {result.stderr}")
        raise RuntimeError(result.stderr)

    pr_url = result.stdout.strip()
    logger.info(f"Created PR: {pr_url}")
    return pr_url

