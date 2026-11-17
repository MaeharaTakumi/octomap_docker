# octomap_docker

走行しながら OctoMap を作り、RViz2 で表示するコンテナ（ROS 2 Humble、`octomap_server`・`octomap_rviz_plugins`）。
点群と TF は Gazebo（コンテナ `20261002`）と自己位置推定（コンテナ `test`、[localizer_docker](https://github.com/MaeharaTakumi/localizer_docker)）が出すものを使う。

（作成中。使い方は段階 4 で書き足す）

## Installation
Docker 23.0 以降が必要

### ビルドとコンテナ作成（Dockerfile がある階層で実行）
```
docker compose up -d --build
```
コンテナに入る:
```
docker exec -it octomap bash
```

## Host 側の .bashrc に以下を追記:
```
xhost +local:
```
