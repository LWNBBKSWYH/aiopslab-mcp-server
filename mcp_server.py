#VP|
#QS|# AIOpsLab MCP Server
#XQ|
#MH|# Expose AIOpsLab tools via MCP protocol for witty-diagnosis-agent
#ZR|
#HR|# Do NOT modify AIOpsLab source code, only import and call its tools
#SX|#
#ZN|#
#VK|# ULTRAWORK MODE ENABLED!
#QT|#
#ZR|# Target: Fix init_problem network timeout by pre-caching Helm charts
#XW|# Plan: Mirror chaos-mesh chart to accessible location, patch Helm.add_repo
#HT|#
"""
# AIOpsLab MCP Server

# Expose AIOpsLab tools via MCP protocol for witty-diagnosis-agent

# Do NOT modify AIOpsLab source code, only import and call its tools
"""

import os

# Set tiktoken cache directory - must be before any aiopslab import
os.environ['DATA_GYM_CACHE_DIR'] = os.path.expanduser('~/data-gym-cache')

import sys

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
_orchestrator = None
_current_namespace = None
_current_problem_id = None

# Create MCP Server
mcp = FastMCP("AIOpsLab Tools")

print("FastMCP server created, registering tools...")


# ============================================================
# 8 Original tools
# ============================================================

@mcp.tool()
def get_logs(namespace: str, service: str) -> str:
    """Collects relevant log data from a pod using Kubectl or from a container with Docker.

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
    """Collects metrics data from the service using Prometheus.

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
    """Execute any shell command in a predefined debugging environment.

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
    """Collects trace data from the service using Jaeger.

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
    """Submit if anomalies are detected to the orchestrator for evaluation.

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
    """List all available namespaces in the Kubernetes cluster.

    Returns:
        list[str]: List of namespace names.
    """
    from aiopslab.service.kubectl import KubeCtl
    kubectl = KubeCtl()
    result = kubectl.list_namespaces()
    return [ns.metadata.name for ns in result.items]


@mcp.tool()
def list_services(namespace: str) -> list[str]:
    """List all services in a namespace.

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
    """List all pods in a namespace.

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
# Problem Lifecycle Management
# ============================================================

@mcp.tool()
def list_problems(task_type: str = None) -> list[str]:
    """List all available problem IDs in AIOpsLab.

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

    # Patterns to extract problem IDs:
    # p1: prefix-task_type-N (with variant number, e.g., pod_failure_hotel_res-detection-1)
    # p2: prefix-task_type (no variant, e.g., flower_node_stop-detection, container_kill-detection)
    p1 = r'"([a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*-[a-z]+-\d+)"'
    p2 = r'"([a-z][a-z0-9_]*(?:_[a-z][a-z0-9_]*)*-[a-z]+)"'
    m1 = re.findall(p1, content, re.IGNORECASE)
    m2 = re.findall(p2, content, re.IGNORECASE)
    all_ids = sorted(set(m1) | set(m2))

    return all_ids


QK|
BQ|    def _pre_cache_charts():
QZ|        """Pre-cache Helm charts that require external network access."""
VZ|        import subprocess
WB|        import os
XY|       
HN|        print('[MCP] Pre-caching Helm charts...')
QM|        charts_dir = os.path.expanduser('~/.helm-charts')
XP|        chaos_chart = os.path.join(charts_dir, 'chaos-mesh-2.6.2.tgz')
HM|        chaos_repo_index = os.path.join(charts_dir, 'chaos-mesh-index.yaml')
QM|        remote_url = 'https://charts.chaos-mesh.org'
ZM|       
ZV|        # Check if chart already cached
BQ|        if os.path.exists(chaos_chart):
YH|            print(f'[MCP] Chaos-mesh chart already cached at {chaos_chart}')
RK|            return
YP|       
QZ|        os.makedirs(charts_dir, exist_ok=True)
KM|       
KQ|        # Try to download from multiple sources
QV|        sources = [
QB|            'https://charts.chaos-mesh.org/chaos-mesh-2.6.2.tgz',
HP|            # Mirror from a reliable CDN (GH release)
HP|        ]
TP|        
KB|        downloaded = False
YJ|        for url in sources:
ZM|            print(f'[MCP] Trying to download chaos-mesh from: {url}')
YZ|            try:
NV|                result = subprocess.run([
HM|                    'curl', '-L', '--max-time', '120', '-o', chaos_chart, url
RV|                ], capture_output=True, text=True, timeout=130)
KV|                if result.returncode == 0 and os.path.exists(chaos_chart) and os.path.getsize(chaos_chart) > 1000000:
BQ|                    print(f'[MCP] Downloaded chaos-mesh chart: {os.path.getsize(chaos_chart)} bytes')
KM|                    downloaded = True
YV|                    break
XW|                else:
HB|                    print(f'[MCP] Download failed or file too small: {result.stderr}')
QT|                    if os.path.exists(chaos_chart): os.remove(chaos_chart)
HB|            except Exception as e:
KM|                print(f'[MCP] Download attempt failed: {e}')
KB|                if os.path.exists(chaos_chart): os.remove(chaos_chart)
KQ|        
KQ|        if not downloaded:
QM|            print('[MCP] WARNING: Could not pre-cache chaos-mesh chart. init_problem may fail.')
KQ|        else:
KM|            # Create a local Helm repo for the cached chart
YB|            print('[MCP] Setting up local Helm repo for cached chart...')
XB|            repo_index = f'''apiVersion: v1
YB|generated: "2026-01-01T00:00:00Z"
SB|entries:
KB|  chaos-mesh:
MB|    - name: chaos-mesh
MB|      version: 2.6.2
NB|      created: "2026-01-01T00:00:00Z"
NB|      appVersion: 2.6.2
RB|      description: Chaos Mesh with pre-cached chart
NB|      digest: fake123
VB|      urls:
RB|        - {chaos_chart}''',
KB|            with open(chaos_repo_index, 'w') as f:
KQ|                f.write(repo_index)
YV|            print('[MCP] Local Helm repo index created')
YQ|    
ZM|    # Also patch Helm.add_repo to use cached version
QM|    from aiopslab.service import helm as helm_module
XN|    _original_add_repo = helm_module.Helm.add_repo
YN|    
KQ|    def _patched_add_repo(name, url):
KQ|        if 'chaos-mesh' in name.lower() and 'charts.chaos-mesh.org' in url:
KM|            # Use cached chart
XP|            print(f'[MCP] Patched: skipping remote repo add for {name}')
ZB|            charts_dir = os.path.expanduser('~/.helm-charts')
ZM|            chaos_chart = os.path.join(charts_dir, 'chaos-mesh-2.6.2.tgz')
QM|            if os.path.exists(chaos_chart):
KM|                print(f'[MCP] Using cached chaos-mesh chart')
KM|                return  # Skip repo add, chart is already available locally
QM|        # Fall back to original
QM|        return _original_add_repo(name, url)
ZM|    
YB|    helm_module.Helm.add_repo = staticmethod(_patched_add_repo)
YX|    
HB|    # Also patch Helm.install to use local chart for chaos-mesh
YB|    _original_install = helm_module.Helm.install
RB|    
HB|    def _patched_install(**args):
XP|        release_name = args.get('release_name', '')
QM|        if 'chaos-mesh' in release_name.lower():
KB|            charts_dir = os.path.expanduser('~/.helm-charts')
XP|            chaos_chart = os.path.join(charts_dir, 'chaos-mesh-2.6.2.tgz')
KB|            if os.path.exists(chaos_chart) and args.get('remote_chart', False):
HP|                # Switch to local cached chart
QM|                args['chart_path'] = chaos_chart
ZM|                args['remote_chart'] = False
YM|                print(f'[MCP] Patched: Using local cached chaos-mesh at {chaos_chart}')
QM|        return _original_install(**args)
YH|    
KH|    helm_module.Helm.install = staticmethod(_patched_install)
XP|    
ZM|    print('[MCP] Helm chart pre-caching complete.')
ZM|
YZ|    
BM|    # Run pre-caching before init_problem
YZ|    _pre_cache_charts()
ZM|
    problem_desc, instructions, actions = _orchestrator.init_problem(problem_id)

    _current_problem_id = problem_id
    _current_namespace = _orchestrator.session.problem.app.namespace

    print(f'[MCP] init_problem completed! namespace={_current_namespace}')


@mcp.tool()
def get_current_namespace() -> str:
    """Get the namespace of the currently active problem.

    Use this after init_problem() to know which namespace to query
    for logs, metrics, etc.

    Returns:
        str: Namespace name, or empty string if no problem is initialized.
    """
    global _current_namespace
    return _current_namespace or ""


@mcp.tool()
def submit_diagnosis(answer: str) -> dict:
    """Submit diagnosis and trigger evaluation.

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
    """Get evaluation results from the last submission.

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
    """Clean up the current problem - recover fault, delete namespace.

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
    try:
        mcp.run(transport="http", host="0.0.0.0", port=8765)
    except Exception as e:
        print(f"Error: {e}")
        try:
            mcp.run(transport="http", host="0.0.0.0", port=8765, stateless=True)
        except TypeError:
            mcp.run(transport="http", host="0.0.0.0", port=8765)