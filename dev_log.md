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
- 結果（Gazebo と `test` の推定（`env:=gazebo rviz:=false map_path:=.../SC10_4_0.05.pcd`）を起動した状態で）：
  - `octomap` から `/velodyne_points`（frame `velodyne`）・`/tf`（`map` →）・`/tf_static`（`base_footprint` → `base_link` → `velodyne_base_link` → `velodyne`）・
    `/clock` が見え、どれも受信できた（`/tf_static` は transient_local で受ける）。
  - **DDS は 127.0.0.1 の UDP だけ**：`octomap_server`・`rviz2` のソケット（`/proc/<pid>/fd` の inode を `/proc/net/{udp,udp6,tcp,tcp6}` と突き合わせた）は
    各 3 つ（10174・10175 と送信用 1 つ、rviz2 は 10176・10177 と 1 つ）で全部 `127.0.0.1`、TCP なし。ホストの `/proc/net/igmp` で
    239.255.0.1 にはどのインタフェース（lo・enp129s0・docker0）も参加していない。
  - `glxinfo -B`：renderer は `NVIDIA GeForce RTX 5080/PCIe/SSE2`（OpenGL 4.6.0 NVIDIA 595.99.02、direct rendering）。ソフトウェア描画（llvmpipe）ではない。
  - **OpenMP**：`liboctomap.so.1.9.7`（Ubuntu の liboctomap1.9）は libgomp につながっていない（NEEDED は liboctomath・libstdc++・libm・libgcc_s・libc）。
    つまり OctoMap の光線の計算（`computeUpdate`）は 1 スレッドで動く。`octomap_server_node` のプロセスに libgomp が入るのは PCL（`libpcl_common` など）から。
  - 起動時に `Could not open file` の WARN が出るのは、`octomap_path: ""`（読む地図なし）のため。動作には関係ない。
