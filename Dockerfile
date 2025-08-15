# 使用标准Ubuntu镜像
FROM ubuntu:20.04

# 设置非交互模式和时区
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 一次性安装所有必要的系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        git \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        build-essential \
        cmake \
        libgl1-mesa-glx \
        libglib2.0-0 \
        zlib1g-dev \
        swig && \
    rm -rf /var/lib/apt/lists/*

# 升级pip到最新版本
RUN python3 -m pip install --upgrade pip

# 创建Python虚拟环境
RUN python3 -m venv /opt/trademaster-env

# 设置PATH使用虚拟环境
ENV PATH="/opt/trademaster-env/bin:$PATH"

# 首先安装基础数学和科学计算包，避免依赖冲突
RUN pip install --no-cache-dir \
    numpy==1.21.6 \
    packaging \
    setuptools \
    wheel

# 安装PyTorch (CPU版本)
RUN pip install --no-cache-dir \
    torch==1.12.1+cpu \
    torchvision==0.13.1+cpu \
    torchaudio==0.12.1 \
    --extra-index-url https://download.pytorch.org/whl/cpu

# 克隆TradeMaster仓库
RUN git clone https://github.com/TradeMaster-NTU/TradeMaster.git /home/TradeMaster

# 设置工作目录
WORKDIR /home/TradeMaster

# 复制简化的依赖文件并安装
COPY requirements-docker.txt /tmp/requirements-docker.txt
RUN pip install --no-cache-dir -r /tmp/requirements-docker.txt

# 设置环境变量
ENV PYTHONPATH="/home/TradeMaster:${PYTHONPATH}"

# 创建启动脚本
RUN echo '#!/bin/bash\n\
source /opt/trademaster-env/bin/activate\n\
cd /home/TradeMaster\n\
exec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# 设置入口点
ENTRYPOINT ["/entrypoint.sh"]

# 设置默认命令
CMD ["/bin/bash"]