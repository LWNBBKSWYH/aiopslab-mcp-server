# AIOpsLab MCP Server

将 AIOpsLab K8s 诊断工具通过 MCP (Model Context Protocol) HTTP 协议暴露，供 witty-diagnosis-agent 远程调用。

## 项目结构

```
aiopslab-mcp-server/
├── mcp_server.py          # MCP Server 主程序（FastMCP HTTP 模式）
├── requirements.txt       # Python 依赖
├── README.md              # 本文件
└── scripts/               # 辅助脚本
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
| `init_problem` | 初始化故障场景（部署+注错+启动负载） | ❌ 暂时禁用 |
| `get_current_namespace` | 获取当前活跃 namespace | ❌ 暂时禁用 |
| `submit_diagnosis` | 提交诊断并触发评估 | ❌ 暂时禁用 |
| `get_results` | 获取评估结果 | ❌ 暂时禁用 |
| `cleanup_problem` | 清理故障场景 | ❌ 暂时禁用 |

## 已完成的工作

### 1. MCP Server 部署
- 使用 FastMCP 3.2.4 以 HTTP Remote 模式运行在 WSL Ubuntu-22.04
- 端口 `8765`，监听 `0.0.0.0`
- 通过 tmux 持久化运行
- MCP Session 管理（`mcp-session-id` Header）

### 2. 工具注册（9个）
- 原有 8 个工具全部正常注册：`get_logs`、`get_metrics`、`exec_shell`、`get_traces`、`submit`、`list_namespaces`、`list_services`、`list_pods`
- 新增 `list_problems`（懒加载，不依赖 ProblemRegistry）

### 3. witty-diagnosis-agent 配置
- `opencode.json` 中配置为 `type: remote`，URL: `http://172.29.89.45:8765/mcp`（此处需更改为自己的服务地址）
- Skill 文档已更新：
  - `C:\Users\86135\.config\opencode\skills\AIOPSLAB.md` — 9 个工具完整说明 + 工作流
  - `C:\Users\86135\.config\opencode\skills\aiopslab\SKILL.md` — 详细参考文档

### 4. 网络架构
- MCP Server 运行在 WSL（K8s 集群可访问）
- witty-diagnosis-agent 通过 HTTP Remote 模式连接
- 端口转发（`netsh interface portproxy`）已配置（WSL IP: `172.29.89.45`）

## 仍需改进的地方

### 🔴 P0 - 阻断问题

#### 1. 端口转发在 Windows 上不通
**现象**：`Test-NetConnection localhost:8765` 从 Windows 侧连接失败

**原因**：WSL NAT 模式下，`netsh interface portproxy` 依赖 `iphlpsvc` 服务将流量转发给 WSL，但当前配置未能正确建立连接

**影响**：witty-diagnosis-agent 只能通过 WSL IP (`172.29.89.45`) 直接连接，无法用 `localhost:8765`

**解决方向**：
- 方案 A：修复 portproxy 配置，确保 Windows → `localhost:8765` → WSL NAT 正确转发
- 方案 B：使用 WSL 侧反向代理（如 nginx/caddy 监听 WSL IP），witty-diagnosis-agent 配置为 `http://<WSL_IP>:8765/mcp`
- 方案 C：迁移 MCP Server 到 Windows 直接运行（需解决 K8s 访问问题）

#### 2. Problem Lifecycle 工具全部禁用（init_problem/submit_diagnosis/get_results/cleanup_problem）
**现象**：这 5 个工具因导入链挂起无法注册

**根因**：`aiopslab.orchestrator.evaluators.quantitative` 模块在 import 时调用 `tiktoken.encoding_for_model()`，该函数需要从 `openaipublic.blob.core.windows.net` 下载 BPE 模型文件（约 400KB），但 WSL 环境无法访问该地址，导致导入挂起 60 秒后超时

**影响**：无法完成端到端的故障诊断流程（初始化 → 诊断 → 提交 → 获取结果 → 清理）

**解决方向**：
- 方案 A（推荐）：在 WSL 环境中预先下载 tiktoken 模型文件到本地缓存
  ```bash
  # 在 WSL 中预先触发下载
  python3 -c "import tiktoken; tiktoken.encoding_for_model('gpt-3.5-turbo')"
  ```
- 方案 B：修改 AIOpsLab 源码，将 `tiktoken` 改为延迟导入（但受约束"不修改 AIOpsLab 源码"）
- 方案 C：将这些工具实现为独立进程，通过 RPC 调用，避免在 MCP Server 启动时导入
- 方案 D：配置 WSL 访问外网代理，使 tiktoken 能正常下载模型

### 🟡 P1 - 重要但非阻断

#### 3. Windows 防火墙规则
- 需要确保 `netsh interface portproxy` 的入站规则被允许
- 考虑添加防火墙入站例外：`netsh advfirewall firewall add rule name="AIOpsLab MCP" dir=in action=allow protocol=TCP localport=8765`

#### 4. MCP Server 开机自启
- 目前 MCP Server 通过 tmux 会话运行，手动执行启动命令
- 建议配置 systemd 服务或 Windows 任务计划程序实现开机自启

#### 5. 日志和监控
- MCP Server 缺乏结构化日志
- 建议添加访问日志（请求计数、错误率、延迟）
- 上报指标到 Prometheus（可选）

## 快速开始

### 1. 启动 MCP Server（在 WSL 中，需要同时放置在aiopslab的同目录下）

```bash
# 进入项目目录
cd /aiopslab-mcp-server

# 使用 tmux 启动（持久化）
tmux new-session -d -s mcp 'python3 mcp_server.py'

# 验证运行状态
tmux capture-pane -t mcp -p | tail -5
# 预期输出: Uvicorn running on http://0.0.0.0:8765 (Press CTRL+C to quit)

# 检查端口监听
ss -tln | grep 8765
# 预期输出: LISTEN 0 2048 0.0.0.0:8765 0.0.0.0:*
```

### 2. 配置 witty-diagnosis-agent

在 `opencode.json` 中添加 MCP 配置：

```jsonc
{
  "mcp": {
    "aiopslab": {
      "type": "remote",
      "url": "http://172.29.89.45:8765/mcp",#这里改为自己的WSL IP地址。或配置为localhost，但需要进行端口转发（下文说明）
      "enabled": true,
      "timeout": 60000
    }
  },
  "plugin": [
    "file:///D:/nodejs/node_global/node_modules/witty-diagnosis-agent/dist/index.js"
  ]
}
```

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

#或者直接用自然语言输入“调用aiopslab这个mcp”
```

### 4. 验证工具注册

在 WSL 中运行验证脚本：

```bash
cd /aiopslab-mcp-server
python3 verify.py
# 预期: Total tools: 9
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

# 添加转发规则（WSL IP: windows的powershall中运行wsl hostname -I获取）
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
tmux new-session -d -s mcp 'cd /aiopslab-mcp-server && python3 mcp_server.py'

# 测试工具调用
cd /aiopslab-mcp-server
python3 verify.py
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
  │──── POST /mcp (tools/list) ──────→│  返回工具列表 (9 tools)
  │←─── SSE response ─────────────────│
  │                                   │
  │──── POST /mcp (tools/call) ──────→│  执行工具
  │←─── SSE response ─────────────────│
```

所有请求需携带 `mcp-session-id` Header（除 initialize 外）。

## 文件索引

| 文件 | 说明 |
|------|------|
| `E:\桌面\AiOps\aiopslab-mcp-server\mcp_server.py` | MCP Server 主程序 |
| `E:\桌面\AiOps\aiopslab-mcp-server\verify.py` | 工具注册验证脚本 |
| `E:\桌面\AiOps\aiopslab-mcp-server\parse_registry.py` | 无依赖的问题列表解析工具 |
| `C:\Users\86135\.config\opencode\skills\AIOPSLAB.md` | Skill 文档（扁平面） |
| `C:\Users\86135\.config\opencode\skills\aiopslab\SKILL.md` | Skill 文档（目录结构） |

## TODO

- [ ] 解决 Windows 端口转发问题，实现 `localhost:8765` 访问
- [ ] 解决 tiktoken 网络依赖，预加载 BPE 模型，启用 Problem Lifecycle 工具
- [ ] 配置 MCP Server 开机自启
- [ ] 添加防火墙入站规则
- [ ] 实现端到端故障诊断流程（init → diagnose → submit → get_results → cleanup）