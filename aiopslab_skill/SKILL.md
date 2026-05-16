---
name: aiopslab
description: Access AIOpsLab K8s diagnostic tools (get_logs, get_metrics, exec_shell, get_traces, submit, list_namespaces, list_services, list_pods, list_problems, init_problem, submit_diagnosis, get_results, cleanup_problem) via MCP HTTP. Use these to investigate microservices deployed in K8s clusters.
version: 1.1.0
category: kubernetes
tags:
  - kubernetes
  - k8s
  - diagnostics
  - monitoring
  - aiopslab
  - fault-injection
  - problem-lifecycle
mcp:
  aiopslab:
    url: http://172.29.89.45:8765/mcp
    type: remote
---

# AIOpsLab K8s Diagnostic Tools

Access the full suite of AIOpsLab diagnostic tools through the `aiopslab` MCP server (remote HTTP transport, running in WSL on `172.29.89.45:8765`).

## Available Tools

### 问题管理工具

| Tool | When to Use | Arguments |
|------|-------------|-----------|
| `list_problems` | When you need to retrieve all available problem IDs | `{"task_type":"detection"}` (optional filter) |
| `init_problem` | When you need to initialize a problem - deploy app, inject fault, start workload | `{"problem_id":"..."}` |
| `get_current_namespace` | When you need to know which namespace is currently active | `{}` |
| `submit_diagnosis` | When you have a diagnosis and want to trigger evaluation | `{"answer":"..."}` |
| `get_results` | When you need to get evaluation results | `{}` |
| `cleanup_problem` | When you need to clean up the current problem | `{}` |

### 集群探索工具

| Tool | When to Use | Arguments |
|------|-------------|-----------|
| `list_namespaces` | When you need to discover all available namespaces in the cluster | `{}` |
| `list_services` | When you need to see all services in a namespace | `{"namespace":"..."}` |
| `list_pods` | When you need to list pods for troubleshooting or inspection | `{"namespace":"..."}` |

### 诊断工具

| Tool | When to Use | Arguments |
|------|-------------|-----------|
| `get_logs` | When you need to see pod logs to understand application behavior or errors | `{"namespace":"...","service":"..."}` |
| `get_metrics` | When you need CPU/memory/network metrics to spot resource anomalies | `{"namespace":"...","duration":5}` |
| `get_traces` | When you need distributed trace data to understand request flows | `{"namespace":"...","duration":5}` |
| `exec_shell` | When you need to run kubectl commands, check pod status, or do debugging | `{"command":"...","timeout":30}` |
| `submit` | When you have a diagnosis conclusion and want to end the session | `{"has_anomaly":"Yes"}` |

## Usage

Load this skill first, then call tools via `skill_mcp`:

```bash
# 列出所有可用问题
skill_mcp(mcp_name="aiopslab", tool_name="list_problems", arguments='{}')
skill_mcp(mcp_name="aiopslab", tool_name="list_problems", arguments='{"task_type":"detection"}')

# 初始化问题（需要 K8s 集群）
skill_mcp(mcp_name="aiopslab", tool_name="init_problem", arguments='{"problem_id":"flower_node_stop-detection"}')
skill_mcp(mcp_name="aiopslab", tool_name="get_current_namespace", arguments='{}')

# 发现集群结构
skill_mcp(mcp_name="aiopslab", tool_name="list_namespaces", arguments='{}')

# 列出 namespace 中的服务
skill_mcp(mcp_name="aiopslab", tool_name="list_services", arguments='{"namespace":"test-hotel"}')

# 列出 namespace 中的 pod
skill_mcp(mcp_name="aiopslab", tool_name="list_pods", arguments='{"namespace":"test-hotel"}')

# 获取 pod 日志
skill_mcp(mcp_name="aiopslab", tool_name="get_logs", arguments='{"namespace":"test-hotel","service":"user"}')

# 获取指标
skill_mcp(mcp_name="aiopslab", tool_name="get_metrics", arguments='{"namespace":"test-hotel","duration":10}')

# 获取追踪
skill_mcp(mcp_name="aiopslab", tool_name="get_traces", arguments='{"namespace":"test-hotel","duration":10}')

# 执行 kubectl 命令
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n test-hotel"}')

# 提交诊断结果
skill_mcp(mcp_name="aiopslab", tool_name="submit", arguments='{"has_anomaly":"Yes"}')

# 提交诊断并获取评估结果（需要先 init_problem）
skill_mcp(mcp_name="aiopslab", tool_name="submit_diagnosis", arguments='{"answer":"Yes"}')
skill_mcp(mcp_name="aiopslab", tool_name="get_results", arguments='{}')

# 清理问题环境
skill_mcp(mcp_name="aiopslab", tool_name="cleanup_problem", arguments='{}')
```

## Workflow for K8s Diagnostics

### 完整问题生命周期

1. **列出问题**: `list_problems` 查看可用故障场景
2. **初始化问题**: `init_problem` 部署应用、注入故障、启动负载
3. **获取 namespace**: `get_current_namespace` 确认活跃的 namespace
4. **发现集群**: `list_namespaces` 查看集群结构
5. **探索服务**: `list_services` 和 `list_pods` 了解应用结构
6. **诊断问题**: `get_logs`、`get_metrics`、`get_traces` 收集证据
7. **深度调查**: `exec_shell` 执行 kubectl 命令
8. **提交诊断**: `submit_diagnosis` 提交答案并触发评估
9. **获取结果**: `get_results` 查看评估结果
10. **清理环境**: `cleanup_problem` 清理问题环境

### 快速诊断（无需 init_problem）

1. **发现集群**: `list_namespaces` 查看可用 namespace
2. **探索服务**: `list_services` 和 `list_pods` 了解结构
3. **收集证据**: `get_logs`、`get_metrics`、`get_traces`
4. **提交结论**: `submit` 提交诊断结果

## Problem ID 格式

```
<problem_type>-<task_type>-<variant>
```

示例：
- `flower_node_stop-detection` - Flower 节点停止故障检测
- `pod_failure_hotel_res-detection-1` - 酒店预订 Pod 故障检测（变体1）
- `astronomy_shop_ad_service_failure-localization-1` - 天文商店广告服务故障定位

## Task Type 说明

| Task Type | Submit 方式 | 示例答案 |
|-----------|-------------|---------|
| **Detection** (`-detection-*`) | `submit` 或 `submit_diagnosis` | `"Yes"` 或 `"No"` |
| **Localization** (`-localization-*`) | `submit_diagnosis` | `'["user-service","order-service"]'` (JSON 数组) |
| **Mitigation** (`-mitigation-*`) | `submit_diagnosis` | `"done"` (完成修复后) |
| **Analysis** (`-analysis-*`) | `submit_diagnosis` | `{"system_level":"...","fault_type":"..."}` (JSON 对象) |

## Common Command Patterns via exec_shell

```bash
# 检查 pod 状态
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n <namespace>"}')

# 描述特定 pod
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl describe pod <pod-name> -n <namespace>"}')

# 检查 pod 事件
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get events -n <namespace> --sort-by=.lastTimestamp"}')

# 获取资源使用情况
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl top pods -n <namespace>"}')

# 检查节点状态
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get nodes"}')

# 检查 service endpoints
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get endpoints -n <namespace>"}')

# 检查 configmaps
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get configmaps -n <namespace>"}')

# 持续监控 pod（带超时）
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n <namespace> -w", "timeout":60}')
```

## Error Handling

If a tool returns an error:
- Check the namespace name is correct (`list_namespaces` first)
- Verify the service name exists in that namespace (`list_services`)
- For exec_shell failures, try a simpler command first
- Check if the pod is actually running (`kubectl get pods`)
- For init_problem failures, verify K8s cluster is accessible (`kubectl cluster-info`)

## Notes

### Flower 问题

Flower 是一个联邦学习应用，包含以下问题：
- `flower_node_stop-detection` - 节点停止故障
- `flower_model_misconfig-detection` - 模型配置错误

### Docker 问题

以下问题不需要 K8s 集群，使用 Docker 部署：
- `flower_node_stop-detection`
- `flower_model_misconfig-detection`
- `container_kill-detection`
- `container_kill-localization`

### Kubernetes 问题

大多数问题需要 K8s 集群：
- `pod_failure_*`、`network_delay_*`、`network_loss_*` 等（使用 Chaos Mesh 注入故障）
- `misconfig_app_*`、`operator_*`、`k8s_target_port_*` 等

## Tool Parameters Reference

### get_logs
```json
{"namespace": "string", "service": "string"}
```

### get_metrics
```json
{"namespace": "string", "duration": 5}
```

### get_traces
```json
{"namespace": "string", "duration": 5}
```

### exec_shell
```json
{"command": "string", "timeout": 30}
```

### list_services / list_pods
```json
{"namespace": "string"}
```

### list_problems
```json
{"task_type": "detection|localization|analysis|mitigation"}
```

### init_problem
```json
{"problem_id": "string"}
```

### submit / submit_diagnosis
```json
{"has_anomaly": "Yes|No"} // submit
{"answer": "string"} // submit_diagnosis
```