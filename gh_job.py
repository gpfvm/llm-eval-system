import subprocess
import json
import os

print("cwd:", os.getcwd())
print("files:", os.listdir())


#1.이슈 가져오기 
    # issue 들 중에서 AI:ready 라벨 있는 것들 가져오기 

def get_issues(repo:str):
    # get issues with Label 
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--label", "AI:ready", "--json", "number"],
            capture_output=True,
            text=True,
            check=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(e.stderr)
  

#get issue contents
def get_issue_content(issue_num:str):
    # gh issue view <issue#>
    result = subprocess.run(
        ["gh", "issue", "view", issue_num, "--json", "title,body"],
        capture_output=True, 
        text=True, 
        check=True
        )
    content = json.loads(result.stdout)
    return content

#Branch cut 
def branch_cut(agent_name:str, model_name:str, issue_num:int):
    # branch cut with  <Agent>_<Model>_issue#
    subprocess.run(["git", "checkout", "-b", f"{agent_name}_{model_name},{issue_num}"],
                    check=True
                )

# temp code commit(hard coding)
def temp_code_test():
    # get_issue_contents , branch_cut test 
    pass 

# Create PR
def create_pr():
    #gh pr create
    subprocess.run(["gh", "pr", "create"],
                        check=True)
    pass


