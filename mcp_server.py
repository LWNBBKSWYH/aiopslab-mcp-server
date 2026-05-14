"""
AIOpsLab MCP Server

将 AIOpsLab 工具通过 MCP 协议暴露，供 witty-diagnosis-agent 调用。

不修改 AIOpsLab 源码，只通过 import 调用其工具函数。
"""

import sys
import os

# Add AIOpsLab path (without modifying its source code)
AIOPSLAB_PATH = os.path.join(os.path.dirname(__file__), "..", "aiopslab", "AIOpsLab")
if os.path.exists(AIOPSLAB_PATH):
    sys.path.insert(0, AIOPSLAB_PATH)
else:
    # Try alternative path
    AIOPSLAB_PATH = "E:\\桌面\\AiOps\\aiopslab\\AIOpsLab"
    sys.path.insert(0, AIOPSLAB_PATH)

from fastmcp import FastMCP

# Global state for session management
# Note: In stateless HTTP mode, these persist only while the server runs
_orchestrator = None
_current_namespace = None
_current_problem_id = None

# Create MCP Server
mcp = FastMCP("AIOpsLab Tools")

print("FastMCP server created, registering tools...")

# ============================================================
# Original 8 tools (verified working)
# ============================================================

@mcp.tool()
def get_logs(namespace: str, service: str) -> str:
    """
    Collects relevant log data from a pod using Kubectl or from a container with Docker.

    Args:
        namespace (str): The namespace in which the service is running.
        service (str): The name of the service.

    Returns:
        str | dict | list[dicts]: Log data as a structured object or a string.
    """
    from aiopslab.orchestrator.actions.base import TaskActions
    return TaskActions.get_logs(namespace=namespace, service=service)


@mcp.tool()
def get_metrics(namespace: str, duration: int = 5) -> str:
    """
    Collects metrics data from the service using Prometheus.

    Args:
        namespace (str): The namespace in which the service is running.
        duration (int): The number of minutes from now to start collecting metrics until now.

    Returns:
        str: Path to the directory where metrics are saved.
    """
    from aiopslab.orchestrator.actions.base import TaskActions
    return TaskActions.get_metrics(namespace=namespace, duration=duration)


@mcp.tool()
def exec_shell(command: str, timeout: int = 30) -> str:
    """
    Execute any shell command in a predefined debugging environment.

    Note: this is NOT A STATEFUL OR INTERACTIVE shell session. So you cannot
    execute commands like "kubectl edit".

    Args:
        command (str): The command to execute.
        timeout (int): Timeout in seconds for the command execution. Default is 30.

    Returns:
        str: The output of the command.
    """
    from aiopslab.orchestrator.actions.base import TaskActions
    return TaskActions.exec_shell(command=command, timeout=timeout)


@mcp.tool()
def get_traces(namespace: str, duration: int = 5) -> str:
    """
    Collects trace data from the service using Jaeger.

    Args:
        namespace (str): The namespace in which the service is running.
        duration (int): The number of minutes from now to start collecting traces until now.

    Returns:
        str: Path to the directory where traces are saved.
    """
    from aiopslab.orchestrator.actions.base import TaskActions
    return TaskActions.get_traces(namespace=namespace, duration=duration)


@mcp.tool()
def submit(has_anomaly: str) -> str:
    """
    Submit if anomalies are detected to the orchestrator for evaluation.

    Args:
        has_anomaly (str): "Yes" if anomalies are detected, "No" otherwise.

    Returns:
        str: The status of the submission.
    """
    from aiopslab.orchestrator.actions.detection import DetectionActions
    result = DetectionActions.submit(has_anomaly=has_anomaly)
    return str(result)


@mcp.tool()
def list_namespaces() -> list[str]:
    """
    List all available namespaces in the Kubernetes cluster.

    Returns:
        list[str]: List of namespace names.
    """
    from aiopslab.service.kubectl import KubeCtl
    kubectl = KubeCtl()
    result = kubectl.list_namespaces()
    return [ns.metadata.name for ns in result.items]


@mcp.tool()
def list_services(namespace: str) -> list[str]:
    """
    List all services in a namespace.

    Args:
        namespace (str): The namespace to query.

    Returns:
        list[str]: List of service names.
    """
    from aiopslab.service.kubectl import KubeCtl
    kubectl = KubeCtl()
    result = kubectl.list_services(namespace)
    return [svc.metadata.name for svc in result.items]


@mcp.tool()
def list_pods(namespace: str) -> list[str]:
    """
    List all pods in a namespace.

    Args:
        namespace (str): The namespace to query.

    Returns:
        list[str]: List of pod names.
    """
    from aiopslab.service.kubectl import KubeCtl
    kubectl = KubeCtl()
    result = kubectl.list_pods(namespace)
    return [pod.metadata.name for pod in result.items]


# ============================================================
# Problem Lifecycle Management (DISABLED - tiktoken network issue)
# ============================================================

@mcp.tool()
def list_problems(task_type: str = None) -> list[str]:
    """
    List all available problem IDs in AIOpsLab.

    Uses lazy parsing - does NOT import ProblemRegistry to avoid tiktoken hang.

    Args:
        task_type (str): Optional filter - "detection", "localization", "analysis", "mitigation".

    Returns:
        list[str]: List of problem IDs like "pod_failure_hotel_res-detection-1".
    """
    import re

    registry_path = os.path.join(AIOPSLAB_PATH, "aiopslab", "orchestrator", "problems", "registry.py")
    if not os.path.exists(registry_path):
        return [f"Registry file not found at {registry_path}"]

    with open(registry_path, 'r') as f:
        content = f.read()

    # Parse problem IDs from registry.py - pattern: "prefix-task_type-N"
    pattern = r'"([a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*-[a-z]+-\d+)"'
    matches = re.findall(pattern, content, re.IGNORECASE)

    unique_ids = sorted(set(matches))

    if task_type:
        unique_ids = [pid for pid in unique_ids if f"-{task_type}-" in pid]

    return unique_ids


# NOTE: The following tools are temporarily disabled because they require
# importing ProblemRegistry which imports all problem classes, which transitively
# import evaluators.quantitative, which calls tiktoken.encoding_for_model().
# This fails in WSL due to no internet access to openaipublic.blob.core.windows.net.
#
# To re-enable:
#   1. Either pre-download the tiktoken BPE model in the WSL environment
#   2. Or configure network access to openaipublic.blob.core.windows.net from WSL
#
# Then uncomment the @mcp.tool() decorators below.

@mcp.tool()
def init_problem(problem_id: str) -> dict:
    """
    Initialize a problem - deploy app, inject fault, start workload.

    This sets up the environment for diagnosis. After calling this,
    use get_logs(), get_metrics(), exec_shell() to diagnose the issue.

    Args:
        problem_id (str): The problem ID (e.g., "pod_failure_hotel_res-detection-1").
                          Use list_problems() to see available options.

    Returns:
        dict: Contains problem_desc, instructions, namespace, session_id.
    """
    global _orchestrator, _current_namespace, _current_problem_id

    from aiopslab.orchestrator import Orchestrator
    from aiopslab.session import Session

    class MockAgent:
        def __init__(self):
            self.agent_name = "mcp-agent"

    _orchestrator = Orchestrator()
    mock_agent = MockAgent()
    _orchestrator.register_agent(mock_agent, name="mcp-agent")

    problem_desc, instructions, actions = _orchestrator.init_problem(problem_id)

    _current_problem_id = problem_id
    _current_namespace = _orchestrator.session.problem.app.namespace

    return {
        "problem_id": problem_id,
        "problem_desc": problem_desc,
        "instructions": instructions,
        "namespace": _current_namespace,
        "session_id": str(_orchestrator.session.session_id),
        "available_actions": list(actions.keys()) if actions else []
    }


@mcp.tool()
def get_current_namespace() -> str:
    """
    Get the namespace of the currently active problem.

    Use this after init_problem() to know which namespace to query
    for logs, metrics, etc.

    Returns:
        str: Namespace name, or empty string if no problem is initialized.
    """
    global _current_namespace
    return _current_namespace or ""


@mcp.tool()
def submit_diagnosis(answer: str) -> dict:
    """
    Submit diagnosis and trigger evaluation.

    Args:
        answer (str): The diagnosis answer.
                      For detection: "Yes" or "No"
                      For localization: comma-separated service names
                      For analysis: root cause description
                      For mitigation: actions taken

    Returns:
        dict: Contains status and evaluation results.
    """
    global _orchestrator, _current_namespace

    if _orchestrator is None or _orchestrator.session is None:
        return {"error": "No active problem. Call init_problem() first."}

    _orchestrator.session.set_solution(answer)

    duration = _orchestrator.session.get_duration() if _orchestrator.session.start_time else 0
    results = _orchestrator.session.problem.eval(
        _orchestrator.session.solution,
        _orchestrator.session.history,
        duration
    )

    _orchestrator.session.set_results(results)
    _orchestrator.session.to_json()

    return {
        "status": "evaluated",
        "results": results,
        "session_id": str(_orchestrator.session.session_id)
    }


@mcp.tool()
def get_results() -> dict:
    """
    Get evaluation results from the last submission.

    Returns:
        dict: Contains evaluation metrics (TTD, TTL, TTA, TTM depending on task type).
    """
    global _orchestrator

    if _orchestrator is None or _orchestrator.session is None:
        return {"error": "No active session. Call init_problem() and submit_diagnosis() first."}

    return {
        "results": _orchestrator.session.results,
        "session_id": str(_orchestrator.session.session_id),
        "problem_id": _current_problem_id
    }


@mcp.tool()
def cleanup_problem() -> str:
    """
    Clean up the current problem - recover fault, delete namespace.

    Returns:
        str: Status of cleanup.
    """
    global _orchestrator, _current_namespace, _current_problem_id

    if _orchestrator is None:
        return "No active problem to clean up."

    try:
        _orchestrator.session.problem.recover_fault()
        _orchestrator.session.problem.app.cleanup()
    except Exception as e:
        return f"Cleanup warning: {str(e)}"

    _orchestrator = None
    _current_namespace = None
    _current_problem_id = None

    return "Problem cleaned up successfully."


if __name__ == "__main__":
    print("Starting AIOpsLab MCP Server on http://0.0.0.0:8765")
    # 使用 stateless 模式
    try:
        mcp.run(
            transport="http",
            host="0.0.0.0",
            port=8765,
            stateless=True  # 启用无状态模式
        )
    except TypeError:
        mcp.run(transport="http", host="0.0.0.0", port=8765)