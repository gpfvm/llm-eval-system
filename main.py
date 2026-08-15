from Ochestrization.gh_job import *
from pipeline import *

if __name__ == "__main__":
    REPO = "gpfvm/llm-eval-system"

    ready_issues = get_issues(REPO)
    logger.info(f"Ready issues: {ready_issues}")

    if ready_issues:
        for issue_num in ready_issues:
            pr_url = run_pipeline(REPO, agent_name="cline", model_name="sonnet", issue_num=issue_num)
            print(pr_url)
    else:
        logger.info("No issues with 'AI:ready' label found.")