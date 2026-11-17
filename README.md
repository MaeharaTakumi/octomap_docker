# octomap_docker

走行しながら OctoMap を作り、RViz2 で表示するコンテナ（ROS 2 Humble、`octomap_server`・`octomap_rviz_plugins`）。
点群と TF は Gazebo（コンテナ `20261002`）と自己位置推定（コンテナ `test`、[localizer_docker](https://github.com/MaeharaTakumi/localizer_docker)）が出すものを使う。

（作成中。使い方は段階 4 で書き足す）

## 使い方（Gazebo）
Gazebo（`20261002`）と自己位置推定（`test`、`env:=gazebo`）を起動してから、コンテナの中で:
```
octomap              # env gazebo、RViz あり
octomap gazebo false # RViz なし
```
`octomap_params [env]` で `config/param/<env>/params.yaml` を開く（ホストの `config/` と同じファイル。起動し直せば反映される）。

launch を直接使うとき（`throttle`・`log_level` も付けられる）:
```
ros2 launch /root/octomap/config/octomap.launch.py env:=gazebo rviz:=true throttle:=false log_level:=info
```
* `throttle:=true`：点群を topic_tools の throttle で間引いてから octomap_server に渡す（レートは `params.yaml` の `cloud_throttle.msgs_per_sec`）。
  解像度 0.05 m では 1 コアで間に合わない（点群の 8 割を捨てる）ので、1 Hz に間引く（`dev_log.md` の 3）
* `log_level:=debug`：octomap_server が点群の挿入・地図の配信にかかった時間を出す

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
