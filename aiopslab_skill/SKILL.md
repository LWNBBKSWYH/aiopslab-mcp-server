---
name: aiopslab
description: Access AIOpsLab K8s diagnostic tools (get_logs, get_metrics, exec_shell, get_traces, submit, list_namespaces, list_services, list_pods, list_problems) via MCP HTTP. Use these to investigate microservices deployed in K8s clusters.
version: 1.0.0
category: kubernetes
tags:
  - kubernetes
  - k8s
  - diagnostics
  - monitoring
  - aiopslab
mcp:
  aiopslab:
    url: http://172.29.89.45:8765/mcp
    type: remote
---

# AIOpsLab K8s Diagnostic Tools

Access the full suite of AIOpsLab diagnostic tools through the `aiopslab` MCP server (remote HTTP transport, running in WSL on `172.29.89.45:8765`).

## Available Tools

| Tool | When to Use | Arguments |
|------|-------------|-----------|
| `list_namespaces` | When you need to discover all available namespaces in the cluster | `{}` |
| `list_services` | When you need to see all services in a namespace | `{"namespace":"..."}` |
| `list_pods` | When you need to list pods for troubleshooting or inspection | `{"namespace":"..."}` |
| `list_problems` | When you need to retrieve all available problem IDs | `{"task_type":"detection"}` (optional filter) |
| `get_logs` | When you need to see pod logs to understand application behavior or errors | `{"namespace":"...","service":"..."}` |
| `get_metrics` | When you need CPU/memory/network metrics to spot resource anomalies | `{"namespace":"...","duration":5}` |
| `get_traces` | When you need distributed trace data to understand request flows | `{"namespace":"...","duration":5}` |
| `exec_shell` | When you need to run kubectl commands, check pod status, or do debugging | `{"command":"...","timeout":30}` |
| `submit` | When you have a diagnosis conclusion and want to end the session | `{"has_anomaly":"Yes"}` |

## Usage

Load this skill first, then call tools via `skill_mcp`:

```bash
# Discover cluster structure
skill_mcp(mcp_name="aiopslab", tool_name="list_namespaces", arguments='{}')

# List services in a namespace
skill_mcp(mcp_name="aiopslab", tool_name="list_services", arguments='{"namespace":"test-hotel"}')

# List pods in a namespace
skill_mcp(mcp_name="aiopslab", tool_name="list_pods", arguments='{"namespace":"test-hotel"}')

# List all available problems (or filter by type)
skill_mcp(mcp_name="aiopslab", tool_name="list_problems", arguments='{}')
skill_mcp(mcp_name="aiopslab", tool_name="list_problems", arguments='{"task_type":"detection"}')

# Get pod logs
skill_mcp(mcp_name="aiopslab", tool_name="get_logs", arguments='{"namespace":"test-hotel","service":"user"}')

# Get metrics
skill_mcp(mcp_name="aiopslab", tool_name="get_metrics", arguments='{"namespace":"test-hotel","duration":10}')

# Get traces
skill_mcp(mcp_name="aiopslab", tool_name="get_traces", arguments='{"namespace":"test-hotel","duration":10}')

# Execute kubectl command
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n test-hotel"}')

# Submit diagnosis result
skill_mcp(mcp_name="aiopslab", tool_name="submit", arguments='{"has_anomaly":"Yes"}')
```

## Workflow for K8s Diagnostics

1. **Discover cluster**: `list_namespaces` to see what's available
2. **Explore namespace**: `list_services` and `list_pods` to understand the structure
3. **Check logs**: `get_logs` on suspicious pods
4. **Check metrics**: `get_metrics` for CPU/memory anomalies
5. **Check traces**: `get_traces` for latency/error patterns
6. **Deep dive**: `exec_shell` with targeted kubectl commands
7. **Submit**: `submit` with your diagnosis

## Task Type Notes

- **Detection** (`-detection-*`): Submit `Yes` or `No` — is there an anomaly?
- **Localization** (`-localization-*`): Submit a JSON list of faulty components, e.g. `'["user-service","order-service"]'`
- **Mitigation** (`-mitigation-*`): Fix the issue via `exec_shell`, then submit `"done"`
- **Analysis** (`-analysis-*`): Submit a JSON dict with `system_level` and `fault_type` fields

## Common Command Patterns via exec_shell

```bash
# Check pod status
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n <namespace>"}')

# Describe a specific pod
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl describe pod <pod-name> -n <namespace>"}')

# Check pod events
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get events -n <namespace> --sort-by=.lastTimestamp"}')

# Get resource usage
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl top pods -n <namespace>"}')

# Check node status
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get nodes"}')

# Check service endpoints
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get endpoints -n <namespace>"}')

# Check configmaps
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get configmaps -n <namespace>"}')

# Watch pod status (with timeout)
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n <namespace> -w", "timeout":60}')
```

## Error Handling

If a tool returns an error:
- Check the namespace name is correct (`list_namespaces` first)
- Verify the service name exists in that namespace (`list_services`)
- For exec_shell failures, try a simpler command first
- Check if the pod is actually running (`kubectl get pods`)

## Note on tiktoken (Problem Lifecycle Tools)

The following tools are temporarily disabled due to a network dependency issue in the WSL environment (`tiktoken` needs internet access to `openaipublic.blob.core.windows.net`):
- `init_problem` — Initialize a problem, deploy app, inject fault
- `get_current_namespace` — Get current active namespace
- `submit_diagnosis` — Submit diagnosis and trigger evaluation
- `get_results` — Get evaluation results
- `cleanup_problem` — Clean up the current problem

They will be re-enabled once the network issue is resolved. The core diagnostic tools above are fully functional.