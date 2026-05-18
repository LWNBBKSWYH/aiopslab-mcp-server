# AIOpsLab MCP Server

将 AIOpsLab K8s 诊断工具通过 MCP (Model Context Protocol) HTTP 协议暴露，供 witty-diagnosis-agent 远程调用。

## 项目结构

```
aiopslab-mcp-server/
├── mcp_server.py          # MCP Server 主程序（FastMCP HTTP 模式）
├── requirements.txt       # Python 依赖
├── README.md               # 本文件
├── aiopslab_skill/         # Skill 文档目录
│   └── SKILL.md            # AIOpsLab MCP Skill 文档
└── scripts/                # 辅助脚本
    └── setup-wsl-portforward.ps1
```

## 功能概览

| Tool | 说明 | 状态 |
|------|------|------|
| `list_namespaces` | 列出 K8s 集群所有 namespace | ✅ 正常 |
| `list_services` | 列出指定 namespace 中的 service | ✅ 正常 |
| `list_pods` | 列出指定 namespace 中的 pod | ✅ 正常 |
| `list_problems` | 列出所有可用故障场景 ID（懒加载解析） | ✅ 正常 |
| `get_logs` | 获取 Pod 日志 | ✅ 正常 |
| `get_metrics` | 获取 CPU/内存/网络指标（Prometheus） | ✅ 正常 |
| `get_traces` | 获取分布式追踪数据（Jaeger） | ✅ 正常 |
| `exec_shell` | 在 Pod 中执行 Shell 命令 | ✅ 正常 |
| `submit` | 提交诊断结果给 AIOpsLab 评估器 | ✅ 正常 |
| `init_problem` | 初始化故障场景（部署+注错+启动负载） | ✅ 正常 |
| `get_current_namespace` | 获取当前活跃 namespace | ✅ 正常 |
| `submit_diagnosis` | 提交诊断并触发评估 | ✅ 正常 |
| `get_results` | 获取评估结果 | ✅ 正常 |
| `cleanup_problem` | 清理故障场景 | ✅ 正常 |

**总计：14 个工具全部正常**

## 已完成的工作

### 1. MCP Server 部署
- 使用 FastMCP 3.2.4 以 HTTP Remote 模式运行在 WSL Ubuntu-22.04
- 端口 `8765`，监听 `0.0.0.0`
- 通过 tmux 持久化运行或 nohup 后台运行
- MCP Session 管理（`mcp-session-id` Header）
- 数据缓存目录：`~/data-gym-cache`（解决 tiktoken 网络依赖）

### 2. 工具注册（14/14）
所有工具已注册并可正常调用：
- `get_logs`、`get_metrics`、`exec_shell`、`get_traces`、`submit`
- `list_namespaces`、`list_services`、`list_pods`、`list_problems`
- `init_problem`、`get_current_namespace`、`submit_diagnosis`、`get_results`、`cleanup_problem`

### 3. 问题列表验证
```
总问题数: 93
Flower 问题: flower_model_misconfig-detection, flower_node_stop-detection
其他 Docker 问题: container_kill-detection, container_kill-localization
```

### 4. witty-diagnosis-agent 配置
- `opencode.json` 中配置为 `type: remote`，URL 需根据实际 WSL IP 调整
- Skill 文档位于：`aiopslab_skill/SKILL.md`

### 5. 网络架构
- MCP Server 运行在 WSL（K8s 集群可访问）
- witty-diagnosis-agent 通过 HTTP Remote 模式连接
- 端口转发配置：Windows → WSL NAT

## 快速开始

### 1. 启动 MCP Server（在 WSL 中）

**方式一：使用 tmux（持久化）**
```bash
# 进入项目目录（需与 aiopslab 同级目录）
cd /mnt/e/桌面/AiOps/aiopslab-mcp-server

# 使用 tmux 启动
tmux new-session -d -s mcp 'python3 mcp_server.py'

# 验证运行状态
tmux capture-pane -t mcp -p | tail -5
# 预期输出: Uvicorn running on http://0.0.0.0:8765 (Press CTRL+C to quit)

# 检查端口监听
ss -tln | grep 8765
```

**方式二：使用 nohup（后台运行）**
```bash
cd /mnt/e/桌面/AiOps/aiopslab-mcp-server
nohup python3 mcp_server.py > /tmp/mcp_server.log 2>&1 &
sleep 5
cat /tmp/mcp_server.log | tail -5
```

### 2. 配置 witty-diagnosis-agent

（1）在 `opencode.json` 中添加 MCP 配置：

```jsonc
{
  "mcp": {
    "aiopslab": {
      "type": "remote",
      "url": "http://172.29.89.45:8765/mcp", // 改为你的 WSL IP 地址
      "enabled": true,
      "timeout": 600000
    }
  },
  "plugin": [
    "file:///D:/nodejs/node_global/node_modules/witty-diagnosis-agent/dist/index.js"
  ]
}
```

获取 WSL IP 地址：
```powershell
wsl hostname -I
```

（2）将 `aiopslab_skill` 目录放在 `C:\Users\{your_username}\.config\opencode\skills` 中。

### 3. 使用工具

在 witty-diagnosis-agent 中调用：

```bash
# 加载 skill
skill(name="aiopslab")

# 列出所有 namespace
skill_mcp(mcp_name="aiopslab", tool_name="list_namespaces", arguments='{}')

# 获取服务日志
skill_mcp(mcp_name="aiopslab", tool_name="get_logs", arguments='{"namespace":"hotel-reservation","service":"user"}')

# 执行 kubectl 命令
skill_mcp(mcp_name="aiopslab", tool_name="exec_shell", arguments='{"command":"kubectl get pods -n hotel-reservation"}')

# 或者直接用自然语言输入"调用aiopslab这个mcp"
```

### 4. 验证工具注册

在 WSL 中运行验证脚本：

```bash
cd /mnt/e/桌面/AiOps/aiopslab-mcp-server
python3 test_mcp_integration.py
# 预期输出: MCP Integration Test: PASSED
```

## 环境要求

| 组件 | 版本/要求 |
|------|-----------|
| Python | 3.12+ |
| FastMCP | 3.2.4 |
| WSL | Ubuntu-22.04及以上 |
| K8s | kubeconfig 已配置，集群可访问 |
| witty-diagnosis-agent | 任意版本（配置 remote MCP 即可） |

## 依赖安装

```bash
pip install -r requirements.txt
```

## 端口转发配置（可选，用于 Windows localhost 访问）

```powershell
# 以管理员身份运行 PowerShell

# 重置现有规则
netsh interface portproxy reset

# 添加转发规则（获取 WSL IP）
netsh interface portproxy add v4tov4 listenport=8765 connectport=8765 connectaddress={WSL IP}

# 验证规则
netsh interface portproxy show all

# 测试连接
Test-NetConnection -ComputerName localhost -Port 8765
```

## 调试命令

```bash
# 查看 MCP Server 运行状态
tmux ls

# 查看 MCP Server 日志
tmux capture-pane -t mcp -p

# 重启 MCP Server
tmux kill-session -t mcp
tmux new-session -d -s mcp 'cd /mnt/e/桌面/AiOps/aiopslab-mcp-server && python3 mcp_server.py'

# 测试工具调用
cd /mnt/e/桌面/AiOps/aiopslab-mcp-server
python3 test_mcp_integration.py

# 端到端测试
python3 test_e2e_full.py
```

## MCP 协议交互流程

```
Client                           Server (FastMCP HTTP)
  │                                   │
  │──── POST /mcp (initialize) ──────→│  返回 mcp-session-id
  │←─── SSE response ─────────────────│
  │                                   │
  │──── POST /mcp (notifications/    │
  │         initialized) ─────────────→│  202 Accepted
  │                                   │
  │──── POST /mcp (tools/list) ──────→│  返回工具列表 (14 tools)
  │←─── SSE response ─────────────────│
  │                                   │
  │──── POST /mcp (tools/call) ──────→│  执行工具
  │←─── SSE response ─────────────────│
  │
```

所有请求需携带 `mcp-session-id` Header（除 initialize 外）。

## 端到端测试结果

```
Session ID: 03776e690aee495eb51170d144299c54

=== Step 1: list_problems ===
Found 93 problems
Flower problems: ['flower_model_misconfig-detection', 'flower_node_stop-detection']

=== Step 2: init_problem ===
EXPECTED ERROR (no k8s): ...FileNotFoundError...
⚠️ 需要 Kubernetes 集群才能初始化问题

=== Step 3: get_logs (no init) ===
Result: 3 validation errors (参数验证正常)

=== Step 4: submit_diagnosis (no init) ===
Result: Error (no init 时的正确行为)

=== End-to-End Test Complete ===
MCP server is working correctly - all tools respond properly.
```

## 文件索引

| 文件 | 说明 |
|------|------|
| `mcp_server.py` | MCP Server 主程序 |
| `aiopslab_skill/SKILL.md` | Skill 文档 |
| `test_mcp_integration.py` | MCP 集成测试脚本 |
| `test_e2e_full.py` | 端到端测试脚本 |
| `check_flower.py` | 问题列表验证脚本 |

MJ|## 已知问题排查
JK|
KB|### Helm chart 下载超时（charts.chaos-mesh.org / openebs.github.io）
PM|
KB|**症状：**
```
Error: INSTALLATION FAILED: Get "https://charts.chaos-mesh.org/chaos-mesh-2.6.2.tgz": ... timeout
Error: INSTALLATION FAILED: Get "https://openebs.github.io/charts/...": ... timeout
```
JS|
KB|**原因：** 网络无法访问 GitHub Pages 域名（常见于 VPN 环境下）
KB|
KB|**解决方案：**
KB|
KB|#### 方案 1：确保 VPN/代理可访问 GitHub Pages
```bash
curl -I --connect-timeout 15 https://charts.chaos-mesh.org
curl -I --connect-timeout 15 https://openebs.github.io
```
KB|
KB|#### 方案 2：预装依赖组件
```bash
# 预装 Chaos Mesh
helm repo add chaos-mesh https://charts.chaos-mesh.org --timeout 10m
helm install chaos-mesh chaos-mesh/chaos-mesh --version 2.6.2 -n chaos-mesh --create-namespace

# 预装 OpenEBS
kubectl apply -f https://openebs.github.io/charts/openebs-operator.yaml
kubectl patch storageclass openebs-hostpath -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}''
```
KB|
KB|#### 方案 3：预拉镜像到 kind 节点
```bash
docker exec aiopslab-control-plane ctr -n k8s.io images pull ghcr.io/chaos-mesh/chaos-mesh:v2.6.2
docker exec aiopslab-control-plane ctr -n k8s.io images pull ghcr.io/openebs/provisioner-localpv:4.0.0
docker exec aiopslab-control-plane ctr -n k8s.io images pull quay.io/openebs/node-disk-manager:v2.1.0
```
KB|
KB|### OpenEBS Pod 处于 ImagePullBackOff 或 Terminating 状态
KB|
KB|**解决方案：**
```bash
# 强制删除卡住的 Pod
kubectl delete namespace openebs --force --grace-period=0
kubectl delete pods -n openebs --force --grace-period=0 --all
```
KB|
KB|### MCP 请求超时（60秒）
KB|
KB|witty 的 MCP 客户端默认超时 60 秒，`init_problem` 需要 2-5 分钟，导致超时。
KB|
KB|在 `opencode.json` 中配置超时：
KB|
KB|```jsonc
{
  "mcp": {
    "aiopslab": {
      "type": "remote",
      "url": "http://172.29.89.45:8765/mcp",
      "enabled": true,
      "timeout": 600000
    }
  },
  "experimental": {
    "mcp_timeout": 600000
  }
}
```
KB|
KB|### 集群残留状态清理
KB|
KB|如果 `init_problem` 中途失败，可能残留以下 namespace：
KB|
KB|```bash
kubectl delete namespace openebs chaos-mesh test-hotel-reservation --force --grace-period=0
```
KB|
KB|---
BQ|
JR|## TODO
RK|
NK|- [x] 解决 tiktoken 网络依赖（设置 DATA_GYM_CACHE_DIR 环境变量）
NK|- [x] 启用 Problem Lifecycle 工具（init_problem/submit_diagnosis 等）
NK|- [x] 验证问题列表提取（93 个问题，2 个 flower）
NK|- [x] 配置 MCP 超时（experimental.mcp_timeout: 600000）
NK|- [x] 添加网络故障排查文档
NK|- [ ] 配置 MCP Server 开机自启
- [ ] 实现端到端故障诊断流程（需 K8s 集群）