FROM ghcr.io/astral-sh/uv:python3.11-bookworm

# 安装基础工具
RUN apt-get update && apt-get install -y \
    curl \
    which \
    bash \
    procps \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# 先只复制必要的配置文件
COPY pyproject.toml uv.lock ./



# 运行应用
# CMD ["python", "-m", "xiyan_mcp_server"]