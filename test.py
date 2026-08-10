import gh_job

#test get_issues

issues = gh_job.get_issues("llm-eval-system")
print(issues)

# test get_
for issue in issues:
    content = gh_job.get_issue_content(issue["number"])
    print(content)