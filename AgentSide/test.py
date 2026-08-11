from Ochestrization.gh_job import *
from AgentSide.agent_call import *

REPO = "gpfvm/llm-eval-system"
REPO_PATH = "/Users/seunghyuns/Documents/llm-eval-system"
AGENT_NAME = "cline"
MODEL_NAME = "qwen_3"

#test get_issues

issues = get_issues(REPO)
print(issues)

# test get_issue_content
content = get_issue_content(REPO,issues[0])
print(content)

# test build_prompt

prompt = build_prompt(content)


#test invoke_cline

invoke_cline(REPO_PATH,prompt)


