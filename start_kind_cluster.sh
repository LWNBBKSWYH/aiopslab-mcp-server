#!/bin/bash
# Kind 集群启动与验证脚本

echo "=========================================="
echo "Kind 集群启动与验证"
echo "=========================================="

# 1. 检查 kind 是否安装
echo -e "\n[1/5] 检查 kind 安装..."
if ! command -v kind &> /dev/null; then
    echo "❌ kind 未安装，正在安装..."
    # 安装 kind (Linux amd64)
    curl -Lo /tmp/kind "https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64"
    chmod +x /tmp/kind
    sudo mv /tmp/kind /usr/local/bin/kind
    echo "✅ kind 安装完成"
else
    echo "✅ kind 已安装: $(kind version)"
fi

# 2. 检查 kubectl 是否安装
echo -e "\n[2/5] 检查 kubectl 安装..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl 未安装，正在安装..."
    curl -Lo /tmp/kubectl "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl"
    chmod +x /tmp/kubectl
    sudo mv /tmp/kubectl /usr/local/bin/kubectl
    echo "✅ kubectl 安装完成"
else
    echo "✅ kubectl 已安装: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
fi

# 3. 检查 Docker 是否运行
echo -e "\n[3/5] 检查 Docker 状态..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
else
    if ! docker info &> /dev/null; then
        echo "⚠️ Docker 未运行，尝试启动..."
        sudo service docker start || sudo systemctl start docker
        sleep 2
        if docker info &> /dev/null; then
            echo "✅ Docker 已启动"
        else
            echo "❌ Docker 启动失败，请手动启动"
        fi
    else
        echo "✅ Docker 运行正常"
    fi
fi

# 4. 检查或创建 kind 集群
echo -e "\n[4/5] 检查 kind 集群..."
if kind get clusters 2>/dev/null | grep -q "^default$"; then
    echo "✅ 集群 'default' 已存在"
    echo "   启动集群..."
    kind start cluster --name default 2>/dev/null || echo "   集群已运行"
else
    echo "📦 创建新 kind 集群 'aiopslab'..."
    cat > /tmp/kind-config.yaml << 'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 30080
    protocol: TCP
  - containerPort: 30081
    hostPort: 30081
    protocol: TCP
EOF
    kind create cluster --name aiopslab --config /tmp/kind-config.yaml
    if [ $? -eq 0 ]; then
        echo "✅ 集群 'aiopslab' 创建成功"
    else
        echo "❌ 集群创建失败"
        exit 1
    fi
fi

# 5. 验证集群连接
echo -e "\n[5/5] 验证集群连接..."
export KUBECONFIG=$(kind get kubeconfig --name aiopslab 2>/dev/null || kind get kubeconfig --name default 2>/dev/null)
if kubectl cluster-info &> /dev/null; then
    echo "✅ Kubernetes 集群连接成功"
    echo ""
    echo "集群信息:"
    kubectl cluster-info
    echo ""
    echo "节点列表:"
    kubectl get nodes
else
    echo "❌ 无法连接到 Kubernetes 集群"
    exit 1
fi

echo -e "\n=========================================="
echo "✅ Kind 集群已就绪！"
echo "=========================================="
echo ""
echo "下一步操作:"
echo "1. 启动 MCP Server: cd /mnt/e/桌面/AiOps/aiopslab-mcp-server && python3 mcp_server.py"
echo "2. 在 witty-diagnosis-agent 中调用 aiopslab 进行评测"