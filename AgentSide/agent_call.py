
import textwrap
from pathlib import Path
import subprocess
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Prompt 
def build_prompt(issue:dict):
    """
    Arg : issue from get_issue_content
    Get issue number, issue title, issue body
    """
    return textwrap.dedent(f"""
            You are fixing a GitHub issue in this repository.

            Issue title: {issue['title']}
            Issue body:
            {issue['body']}

            Constraints:
            - Only edit the source and test files needed to fix this issue.
            - Do NOT run any git commands (no add, commit, push, checkout, branch).
            - Do NOT modify anything under .github/workflows/.
            - Write or update relevant tests alongside your code changes.
            - Do not create or modify files outside this repository directory.
        """).strip()


# call cline with yolo mode and make writhe code 
def invoke_cline(repo_path: Path, prompt: str, timeout: int = 900) -> str:
    """Cline을 headless(--yolo) 모드로 호출해 코드를 작성시킨다.

    Cline이 직접 파일을 수정하므로 리턴값은 실행 로그(stdout)이고,
    실제 변경 여부는 호출 후 get_changed_files()로 오케스트레이터가 확인한다.
    """
    logger.info("Cline has been called")
    result = subprocess.run(
        ["cline", "--yolo", prompt],
        cwd=str(repo_path),
        #capture_output=True,
        text=True,
        timeout=timeout,
    )
    logger.info("Cline return code: %s", result.returncode)

    if result.returncode != 0:
        raise RuntimeError(f"Cline invocation failed with return code {result.returncode}")
    logger.info("Cline finished")
    return result.stdout