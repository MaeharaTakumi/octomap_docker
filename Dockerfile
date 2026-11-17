# syntax=docker/dockerfile:1
# OctoMap を作って RViz2 で表示するコンテナ（ROS 2 Humble。Gazebo（20261002）・自己位置推定（test）と同じ版）
# 自分でビルドするコードは無い。設定（launch・パラメータ・RViz）は docker-compose.yml でホストの config/ を割り当てる
FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-c"]

# ---------- ROS 2 Humble（apt リポジトリの追加は localization の Dockerfile と同じ手順） ----------
RUN apt-get update && \
    apt-get install -y \
    curl \
    gnupg \
    tzdata \
    software-properties-common && \
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    add-apt-repository universe && \
    curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" > /etc/apt/sources.list.d/ros2.list && \
    apt-get update && \
    apt-get install -y \
    ros-humble-ros-base \
    ros-humble-rviz2 \
    ros-humble-octomap-server \
    ros-humble-octomap-rviz-plugins \
    ros-humble-topic-tools \
    mesa-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ---------- bashrc（localization の Dockerfile と同じ。ros2_ws は無いので install/setup.bash は読まない） ----------
RUN cat >> ~/.bashrc <<'EOF'
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=11

# 通信設定。使う方だけを有効にし、新しい端末を開く（既存の端末には反映されない）
# --- 実機（LiDAR PC と LAN 越しに通信する） ---
# export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
# unset RMW_IMPLEMENTATION FASTRTPS_DEFAULT_PROFILES_FILE ROS_LOCALHOST_ONLY
# --- Gazebo（同じ PC 内だけで通信し、LAN には出ない） ---
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTRTPS_DEFAULT_PROFILES_FILE=/root/fastdds_localhost.xml
export ROS_LOCALHOST_ONLY=0   # 1 だと共有メモリが追加され、gazebo コンテナと通信できない
unset FASTDDS_BUILTIN_TRANSPORTS
EOF

COPY src/aliases.txt /root/.bash_aliases
COPY src/fastdds_localhost.xml /root/fastdds_localhost.xml
# この README（コマンドの一覧など）をコンテナの中でも読めるようにする
COPY README.md /root/octomap/README.md
