from Ochestrization.gh_job import *
from pipeline import *

if __name__ == "__main__":
    REPO = "gpfvm/test_repo"

    ready_issues = get_issues(REPO)
    logger.info(f"Ready issues: {ready_issues}")

    failed_issues = []

    if ready_issues:
        for issue_num in ready_issues:
            try:
                pr_url = run_pipeline(REPO, agent_name="cline", model_name="qwen", issue_num=issue_num)
                print(pr_url)
            except:
                # fail 하면 어디서 페일 했는지 로그로 남겨야함..
                # issue # failed, skipping.... 
                failed_issues.append(issue_num)
    else:
        logger.info("No issues with 'AI:ready' label found.")