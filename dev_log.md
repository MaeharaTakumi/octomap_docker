# 開発ログ（octomap）

## 2026-11-17

### 1. 土台を作る

- 目的：Gazebo（`20261002`）と自己位置推定（`test`）の点群・TF から、走りながら OctoMap を作って RViz2 で表示するコンテナを用意する。
- やったこと：
  - `Dockerfile`（`ubuntu:22.04` + ROS 2 Humble の `ros-base`・`rviz2`・`octomap-server`・`octomap-rviz-plugins`・`topic-tools`・`mesa-utils`）、
    `docker-compose.yml`（localization と同じ設定。volumes は X11 と `./config`）、`config/`（launch・`param/gazebo/params.yaml`・RViz）、
    `src/aliases.txt`、`src/fastdds_localhost.xml`（localization から複製）を作った。
  - 入ったパッケージの版：octomap_server 2.3.1、octomap_rviz_plugins 2.1.1、octomap_msgs 2.0.1、liboctomap 1.9.7。
  - `octomap_server_node` を単体で起動し、`ros2 param list`・`describe`・`get` でパラメータ 43 項目（`qos_overrides` を除く）の名前・型・既定値を確かめ、
    `params.yaml` に全項目を書いた。初期値から変えたのは `use_sim_time: true`、`resolution: 0.1`（既定 0.05）、`sensor_model.max_range: 20.0`（既定 -1）、
    `latch: false`（既定 true）。
