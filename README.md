# LLM Evaluation System

An issue-driven coding-agent automation pipeline that takes GitHub issues labeled `AI:ready`, asks Cline to implement a fix, and opens a pull request with the resulting changes.

> **Current status:** This is a development prototype. The entry point currently targets `gpfvm/test_repo`, synchronizes against `main`, and uses a Windows-oriented Cline command (`cline.cmd`). Review the configuration before running it against a real repository.

## How It Works

1. **Find ready issues** — Uses the GitHub CLI (`gh`) to list issues with the `AI:ready` label.
2. **Prepare the repository** — Reuses a local clone or clones the target repository next to this project.
3. **Synchronize `main`** — Checks out `main` and pulls the latest changes from `origin`.
4. **Create a working branch** — Creates a branch named `<agent>_<model>_issue<issue-number>`.
5. **Invoke the coding agent** — Builds a prompt from the issue body and invokes Cline to modify the repository.
6. **Commit and inspect changes** — Stages changes, creates a commit, and captures its diff.
7. **Push and open a pull request** — Pushes the branch and creates a PR targeting `main`, with the issue referenced in the PR body.
8. **Clean up on failure** — Attempts to restore the working tree, switch back to `main`, and delete the newly created branch.

## Project Structure

```text
.
├── main.py                    # Entry point: processes AI:ready issues
├── pipeline.py                # End-to-end issue-to-pull-request workflow
├── pipeline_test.py           # Tests for pipeline cleanup behavior
├── conftest.py                # Temporary local Git repository fixture
├── AgentSide/
│   ├── agent_call.py          # Prompt construction and Cline invocation
│   └── test.py                # Agent invocation tests
└── Ochestrization/
    ├── gh_job.py              # GitHub CLI and Git operations
    └── test.py                # Tests for orchestration helpers
```

## Prerequisites

- Python 3
- Git
- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated with permission to read issues, push branches, and create pull requests
- [Cline CLI](https://github.com/cline/cline) available as `cline.cmd`
- An Ollama setup with the configured model `qwen3:8b` available to Cline

Verify the command-line tools before running:

```powershell
git --version
gh --version
gh auth status
cline.cmd --help
ollama list
```

The agent invocation currently passes `-P ollama` and `-m qwen3:8b` to Cline. Adjust `AgentSide/agent_call.py` if your Cline CLI version or provider configuration differs.

## Setup

Clone this repository and enter its directory:

```powershell
git clone https://github.com/gpfvm/llm-eval-system.git
cd llm-eval-system
git checkout dev_win
```

Create and activate a virtual environment, then install the test dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pytest
```

The current source imports standard-library modules and uses external command-line tools for GitHub, Git, and Cline. Add any project dependencies to a dependency file as the project grows.

## Configuration

The current entry point in `main.py` contains the target repository directly:

```python
REPO = "gpfvm/test_repo"
```

It then calls the pipeline with `agent_name="cline"` and `model_name="qwen"`. Update `REPO` to the repository you intend to automate. Ensure that repository has a `main` branch and that your GitHub CLI account has the required access.

The orchestration code expects the target repository to be cloned into a sibling directory of this project by default. You can change this behavior by passing an explicit path to `prepare_repo`.

## Run

After completing the prerequisites and reviewing the target repository configuration:

```powershell
python main.py
```

The script searches for issues carrying the `AI:ready` label, attempts to run the pipeline for each issue, logs failures, and continues to the next issue.

**Important:** Running this command can modify a repository, create commits, push branches, and open pull requests. Test with a disposable repository before using it on a production project.

## Tests

Run the test suite from the project root:

```powershell
python -m pytest
```

The tests cover orchestration helpers such as issue retrieval, branch creation, commit/diff generation, branch pushing, pull-request creation, and cleanup behavior. Several GitHub CLI operations are mocked; passing tests does not verify the entire workflow against a live GitHub repository or a running Cline/Ollama setup.

## Implementation Notes

- The issue body is used as the main task prompt. The generated prompt instructs the agent to limit changes to relevant source and test files, avoid Git commands, avoid modifying `.github/workflows/`, and stay inside the repository.
- Git operations and pull-request creation are handled by the GitHub CLI and Git subprocesses.
- The current cleanup routine attempts to check out `main` and delete the working branch after a pipeline error. It should be reviewed before use with repositories containing pre-existing local changes.
- The current `main.py` prints the value returned by `run_pipeline` (a result dictionary containing the commit SHA, diff, and PR URL), rather than printing only the PR URL.

## Contributing

1. Create a branch for your change.
2. Add or update tests for the affected behavior.
3. Run `python -m pytest`.
4. Open a pull request describing the change and its test coverage.
