from AgentSide.agent_call import *
import pytest
import subprocess
from unittest.mock import patch

REPO = "gpfvm/test_repo"
AGENT_NAME = "cline"
MODEL_NAME = "qwen_3"

@patch("AgentSide.agent_call.subprocess.run")
def test_invoke_cline_time_out(mock_run):
    """
    Test case : Agent timeout

    call agent
    Time out 
    Error must be raised with "Time out"
    """
    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["cline"], timeout=900)
    with pytest.raises(RuntimeError):
        invoke_cline("/fake/path","propmt")
    

