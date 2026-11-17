# octomap_docker
走行しながら OctoMap を作り、RViz2 で表示するコンテナ（ROS 2 Humble、`octomap_server`・`octomap_rviz_plugins`）

点群（`/velodyne_points`）と TF（`/tf`・`/tf_static`）・時刻（`/clock`）は、Gazebo（コンテナ `20261002`）と
自己位置推定（コンテナ `test`、[localizer_docker](https://github.com/MaeharaTakumi/localizer_docker)）が出すものを使う。
今の対象は Gazebo だけ（実機は下の「実機で使う場合」）。地図の保存（.bt）と 2D の地図は扱わない。

|入っているもの|版（2026-11-17 のビルド）|
|:--|:--|
|`ros-humble-ros-base`・`ros-humble-rviz2`||
|`ros-humble-octomap-server`|2.3.1（liboctomap 1.9.7。OpenMP なし）|
|`ros-humble-octomap-rviz-plugins`|2.1.1|
|`ros-humble-topic-tools`|1.1.2（点群の間引き）|
|`mesa-utils`|`glxinfo`|

自分でビルドするコードは無い。設定（launch・パラメータ・RViz）は `config/` に置き、`docker-compose.yml` でコンテナの
`/root/octomap/config` に割り当てる（**ホストで直せば、起動し直すだけで反映される**。イメージの作り直しは要らない）。

## 2026/02/20現在で確認している不具合
### 最新GPU搭載(NVIDIA GeForce RTX 50xx 等)のPCで描画が不安定

原因: コンテナのOS(Ubuntu22.04)が最新GPUを識別不能なため

対策: 本Dockerコンテナを`run`したあと，**コンテナ内の**`.bashrc`に以下を追記:
```
export MESA_LOADER_DRIVER_OVERRIDE=zink
```
**動作確認済みGPU**（localizer_docker で確認）

RTX 5070 Ti Laptop

（このリポジトリの開発に使った RTX 5080 では、追記しなくても `glxinfo -B` の renderer が NVIDIA になった。`dev_log.md` の 1）

## Installation
Docker 23.0 以降が必要

### ビルドとコンテナ作成(Dockerfileがある階層で実行)
```
docker compose up -d --build
```
コンテナに入る:
```
docker exec -it octomap bash
```

### (docker compose を使わない場合)
```
docker build -t octomap_maehara:latest .
```
```
docker run -itd --ipc=host --gpus=all --env="NVIDIA_DRIVER_CAPABILITIES=all" --net host --privileged -e DISPLAY=unix${DISPLAY} -e NVIDIA_VISIBLE_DEVICES=0 -v /tmp/.X11-unix:/tmp/.X11-unix -v $(pwd)/config:/root/octomap/config --name octomap octomap_maehara:latest
```

## Host側の.bashrc に以下を追記:
```
xhost +local:
```

# 使い方（Gazebo）
起動の順は Gazebo → 自己位置推定 → octomap（TF の map → base は自己位置推定の EKF が出す）。

1. Gazebo（`20261002` の中）: `ros2 launch connection_wheelchair connection_wheelchair.launch.py`
2. 自己位置推定（`test` の中）: `ros2 launch localization_bringup localization.launch.py env:=gazebo rviz:=false map_path:=/root/ros2_ws/map/SC10_4_0.05.pcd`
   （RViz は octomap の方で出すので `rviz:=false`）
3. OctoMap（`octomap` の中）: `octomap`

車椅子を走らせると、RViz に地図が積み上がっていく（`dev_log.md` の 2）。
`test` の中から `python3 /root/ros2_ws/localization_tools/drive/drive_test.py gazebo slalom --yes` で決まった動きで走らせられる
（`drive gazebo ...`（`run_test.sh`）は推定を自分で起動するので、2 の推定が動いているとエラーで止まる）。

## 実行可能コマンド一覧
この README はコンテナの中の `/root/octomap/README.md` にもある（イメージを作るときに写す）。

|コマンド|実行内容|備考|
|:------|:-----|:---|
|`octomap`|OctoMap を作って表示する|octomap_server と rviz2 を起動する。`octomap gazebo` のように環境を付ける（既定 `gazebo`。`config/param/<環境>/params.yaml` を使う）。`octomap gazebo false` で RViz なし|
|`octomap_params`|パラメータを確認/編集*|`octomap_params gazebo`（既定 `gazebo`）。`config/param/<環境>/params.yaml`（octomap_server・rviz2・cloud_throttle の節）を開く。保存して `octomap` を起動し直せば反映される|
|`reload`|terminalの再読込||

*: vscodeにAttachして実行

launch を直接使うとき（引数はどれも省略可）:
```
ros2 launch /root/octomap/config/octomap.launch.py env:=gazebo rviz:=true throttle:=false log_level:=info
```
|引数|既定|内容|
|:--|:--|:--|
|`env`|`gazebo`|`config/param/<env>/params.yaml` を octomap_server・rviz2（・cloud_throttle）に渡す|
|`rviz`|`true`|rviz2（`config/rviz/octomap.rviz`）を起動する|
|`throttle`|`false`|`true` なら点群を topic_tools の throttle で `/velodyne_points_throttle` に間引いてから octomap_server に渡す（レートは `params.yaml` の `cloud_throttle.msgs_per_sec`）|
|`log_level`|`info`|octomap_server のロガーのレベル。`debug` で点群の挿入・地図の配信にかかった時間を出す|

## トピック
|トピック|向き|内容|
|:--|:--|:--|
|`/velodyne_points`|購読（octomap_server の `cloud_in` を付け替え、RViz）|点群。Gazebo の配信は RELIABLE、octomap_server の購読は BEST_EFFORT（互換）|
|`/tf`・`/tf_static`|購読|map → base_footprint（EKF）、base_footprint → … → velodyne（Gazebo の URDF）|
|`/clock`|購読|sim time（`use_sim_time: true`）|
|`/octomap_full`|配信（RViz が購読）|OctoMap（占有・空きの全体）。RViz の OctoMap の表示（octomap_rviz_plugins の OccupancyGrid）|
|`/initial_map`|購読（RViz）|NDT が読み込んだ地図（transient_local）|

octomap_server は購読されたトピックだけを作るので、`/occupied_cells_vis_array`・`/projected_map` などは RViz で購読しない（重くなる）。
RViz の 2D Pose Estimate・2D Goal Pose は外してある（押すと `/initialpose` が自己位置推定の NDT と EKF に届く）。

## パラメータ（`config/param/gazebo/params.yaml`）
octomap_server 2.3.1 のパラメータを全項目書いてある（書いていない項目をコードの既定値で動かさない）。主な値:

|項目|値|備考|
|:--|:--|:--|
|`resolution`|0.1 m|0.05 m では 1 コアで間に合わず点群の 8 割を捨てる（その場合は `throttle:=true` で 1 Hz に間引く。`dev_log.md` の 3）|
|`sensor_model.max_range`|20.0 m|これより遠い点は占有にしない|
|`frame_id`・`base_frame_id`|`map`・`base_footprint`||
|`latch`|false|走りながら作るので、更新のたびに配信する|
|`use_sim_time`|true|Gazebo の `/clock`|
|`cloud_throttle.msgs_per_sec`|1.0|`throttle:=true` のときの点群のレート|

解像度 0.1 m・最大距離 20 m（Gazebo、RTX 5080 の PC）で、地図は点群（10 Hz）ごとに更新され、遅れは平均 0.08 s、octomap_server の CPU は 1 コアの 63 %（`dev_log.md` の 3）。

## 実機で使う場合
`config/param/<色>/params.yaml` を足す（gazebo のものを写し、`use_sim_time: false`、`base_frame_id: base_link` などに直す。3 つの節とも）。
コンテナ内の `~/.bashrc` の通信設定を切り替える（Gazebo 用の行をコメントアウトし、実機用の行のコメントを外す）。新しい terminal で `octomap <色>` を実行する。

# 通信
`.bashrc` の通信設定は localizer_docker と同じ（`ROS_DOMAIN_ID=11`。既定は Gazebo 用で、Fast DDS のプロファイル `/root/fastdds_localhost.xml` により
127.0.0.1 の UDP だけで通信し、LAN には出ない）。`fastdds_localhost.xml` は localizer_docker のものをそのまま写したもの。
