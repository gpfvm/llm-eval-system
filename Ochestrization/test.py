from Ochestrization.gh_job import *

REPO = "gpfvm/llm-eval-system"
REPO_PATH = "/Users/seunghyuns/Documents/llm-eval-system"
AGENT_NAME = "CLINE"
MODEL_NAME = "qwen_3"

#test get_issues

issues = gh_job.get_issues("llm-eval-system")
print(issues)

# test get_
for issue in issues:
    content = gh_job.get_issue_content(issue["number"])
    print(content)