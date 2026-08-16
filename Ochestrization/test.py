from Ochestrization.gh_job import *

REPO = "gpfvm/test_repo"
AGENT_NAME = "cline"
MODEL_NAME = "qwen_3"
REPO_PATH = prepare_repo(REPO)

#test get_issues

issues = get_issues(REPO)
print(issues)

# test get_issue_content
content = get_issue_content(REPO,issues[0])
print(content)

#test prepare_repo
path = prepare_repo(REPO,REPO_PATH)
print(path)

# test sync_main 
#sync_main(path)

#test branch cut
#branch_cut(path, AGENT_NAME, MODEL_NAME, issues[0])


