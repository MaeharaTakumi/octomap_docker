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

### 2. 走りながら地図を作る（Gazebo、slalom）

- 目的：Gazebo の車椅子を走らせ、OctoMap が積み上がっていくことと、TF を待てずに捨てる点群がほぼ無いことを確かめる。
- やったこと：
  - **QoS**：`ros2 topic info -v /velodyne_points` で、配信（`/velodyne/gazebo_ros_laser_controller`）は RELIABLE・VOLATILE、
    octomap_server の購読は BEST_EFFORT・VOLATILE。RELIABLE の配信を BEST_EFFORT で受けるのは互換なので、中継ノードは要らない。
  - 起動の順：Gazebo（`connection_wheelchair.launch.py`）→ `test` の推定（`env:=gazebo rviz:=false map_path:=.../SC10_4_0.05.pcd`）→ octomap（`rviz:=true`）。
  - 走らせ方：はじめ案 A（`test` の中から `drive gazebo slalom check/octomap_slalom_<日時>`）にしたが、`run_test.sh` は推定を自分で起動・停止する作りで、
    推定が既に動いていると「localization processes are still running」で止まる（走行・録画はしていない）。ユーザーの確認のうえ、
    `test` の中から `drive/drive_test.py gazebo slalom --yes` を直接実行した（推定は上で起動したもの。**録画はしていない**）。
    slalom：1.00 m 前進 → スラローム 12.47 s・7.52 m（sim time 49.6〜63.2 s）。
  - RViz の設定を直した：octomap_rviz_plugins 2.1.1 の `OccupancyGrid` は rviz_common の RosTopicDisplay で、トピックのプロパティ名は `Topic`
    （`Octomap Topic` では「Error subscribing: Empty topic name」で購読しない）。視点は車体（`base_link`）を追う見下ろし（Orbit、距離 25 m、Pitch 0.9、Yaw 0）にした。
- 結果：
  - 走行に沿って地図が積み上がる（下図。左から走る前・走行中・走行後。色は高さ、白は今の点群）。床・壁・天井が 0.1 m のボクセルで埋まる。
  - **MessageFilter**（`Message Filter dropping message`、2.5 s に 1 回までの INFO）：octomap_server は走行中 0 件。起動直後（走る前、sim 41.7 s）に
    「queue is full」が 1 件だけ。rviz2 は「the timestamp on the message is earlier than all the data in the transform cache」が起動直後に 1 件。
    （1 回目の試行では、止まっている間に rviz2 の点群の表示だけ「queue is full」が数件出た。octomap_server は 0 件）

![slalom で積み上がる OctoMap](dev_log_images/stage2_slalom.png)

RViz の画面全体（走行後）：

![RViz の画面（走行後）](dev_log_images/stage2_rviz_window.png)
