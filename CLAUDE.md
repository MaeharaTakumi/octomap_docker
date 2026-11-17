# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

今の仕様と作業の決まりだけを書く。経緯（いつ・なぜ変えたか、比べた数値）は `dev_log.md` に任せ、ここには番号で参照する。

## 厳守事項（ユーザー指示）

- **回答・コメント・文書は日本語で書く**。
- **次のものは読むのは可、編集は不可**：`Docker/Gazebo/`、`Docker/localization/`（`src/`・`docker/` を含む）、
  コンテナ `20261002`・`test`・その他の既存のコンテナのファイル。問題を既存側の変更で解決しない。変更が必要に見えたら、作業を止めてユーザーに相談する。
- 既存の構成に対してしてよいのは、**既存のコマンドと launch 引数で起動・停止することだけ**（例：`test` の推定を `rviz:=false` で起動する）。
- **曖昧な点は自分で判断せず、必ずユーザーに質問する。**
- GitHub のリポジトリは `MaeharaTakumi/octomap_docker`（Public、`main`）だけ。他のリポジトリは作らない。
- イメージの再ビルドとコンテナの作り直しは `octomap` に限って確認なしでよい。他のコンテナは起動と停止だけ。
- sudo はこのシェルからは動かない（no new privileges）。必要なとき（例：ホストの `net.core.rmem_max`）は、コマンドを示してユーザーに実行を頼む。
- **作業がひと区切りついたら（動作を確かめ、dev_log と README を直したら）commit して push し、その commit を報告する。**
- **開発ログ `dev_log.md` に、作業したら日付・項目ごとに末尾へ追記する**。各項目は目的・やったこと・結果（数値）・図。説明は簡潔に。
  図は `dev_log_images/` に置いて埋め込む。
- 範囲は「走りながら OctoMap を作って表示する」まで。地図の保存（.bt）と 2D の地図は範囲外。

## コードの書き方（ユーザー指示）

- 冗長なコードを書かない（無駄な条件分岐、try/except など）。
- 日本語のコメントを要所に入れる。関数には、機能と入出力のコメントを入れる。
- 関数の中に値をハードコードしない。launch の値（既定の env・トピック名・ファイル名など）はファイル上部の定数、ノードの値は `params.yaml` にまとめる。
- **`params.yaml` には各ノードの全項目を書く**（書いていない項目をコードの既定値で動かさない。localization と同じ決まり）。項目と既定値は、ノードを起動して
  `ros2 param list`・`describe`・`get` で確かめてから書く。launch が入れる値（throttle の `throttle_type`・`input_topic`・`output_topic`）は yaml のコメントにそう書く。

## 作業場所の構成

`Docker/octomap/` がこのリポジトリ（`MaeharaTakumi/octomap_docker`）。自分でビルドするコードは無い（colcon・`deploy.sh`・`repos.yaml` は作らない）。

| 場所 | 中身 |
|---|---|
| `CLAUDE.md`・`README.md`（使い方）・`dev_log.md`・`dev_log_images/` | 文書 |
| `Dockerfile`・`docker-compose.yml`・`.dockerignore`・`.gitignore` | イメージ・コンテナ。`.dockerignore` で `config/`・`dev_log*`・`.git` をビルドの入力から外す |
| `src/aliases.txt` | コンテナの `/root/.bash_aliases`（`octomap`・`octomap_params`・`reload`） |
| `src/fastdds_localhost.xml` | localization の `docker/src/` から複製（**内容は変えない**）。コンテナの `/root/fastdds_localhost.xml` |
| `config/octomap.launch.py` | octomap_server・rviz2・（`throttle:=true` なら）点群の throttle を起動 |
| `config/param/<env>/params.yaml` | 環境ごとのパラメータ（`octomap_server`・`rviz2`・`cloud_throttle` の節）。今は `gazebo` だけ |
| `config/rviz/octomap.rviz` | RViz の設定 |

- `config/` は compose でコンテナの `/root/octomap/config` に割り当てる。**ホストで直せば、起動し直すだけで反映される**（イメージの作り直しは要らない）。
- 将来の実機：`config/param/<色>/params.yaml` を足し（`use_sim_time: false`、`base_frame_id: base_link` など。3 つの節とも）、`.bashrc` の通信設定を
  切り替えるだけで使う形にしてある。実機用のファイルは今は作らない。
- `.gitignore`：`__pycache__/`・`*.bt`・`*.ot`・`*.pcd`・`*.db3`・`*.mcap`・`*.mp4`。

## コンテナ

| コンテナ | イメージ | 役割 |
|---|---|---|
| `octomap` | `octomap_maehara:latest`（compose のプロジェクト `octomap_maehara`） | **OctoMap を作って表示する（このリポジトリ）** |
| `20261002` | `ubuntu_22_04` | Gazebo（車椅子・ワールド `SC_10_4.world`）。**編集禁止**。点群・URDF の TF・`/clock` を出す |
| `test` | `localizer_maehara:latest` | 自己位置推定（NDT + EKF）。**編集禁止**。TF の map → base_footprint を出す |

- イメージ：`ubuntu:22.04` + ROS 2 Humble（Gazebo・test と同じ版。違う ROS の版の間の通信は保証されない）。`ros-humble-ros-base`・`rviz2`・
  `octomap-server`（2.3.1）・`octomap-rviz-plugins`（2.1.1）・`topic-tools`（1.1.2）・`mesa-utils`。desktop 一式は入れない。
  ROS の apt リポジトリは localization の Dockerfile と同じ手順で足す。
- compose の設定は localization と同じ（host network・ipc host・privileged・GPU・X11・`NVIDIA_DRIVER_CAPABILITIES=all`）。volumes は X11 と `./config` の 2 つだけ。
- 作り直し：`docker compose build` → `docker compose up -d --force-recreate`。そのあと、通信が 127.0.0.1 の UDP だけ（TCP なし、LAN の 239.255.0.1 に参加しない）、
  `glxinfo -B` の renderer が NVIDIA であることを確かめる（`dev_log.md` の 1 の方法）。
- **通信**：`.bashrc` は localization の Dockerfile の bashrc のブロックと同じ（`source /root/ros2_ws/install/setup.bash` だけ除く）。`ROS_DOMAIN_ID=11`、
  既定は Gazebo 用（`RMW_IMPLEMENTATION=rmw_fastrtps_cpp`、`FASTRTPS_DEFAULT_PROFILES_FILE=/root/fastdds_localhost.xml`、`ROS_LOCALHOST_ONLY=0`）。
  実機用はコメントの付け外しで切り替える。test と octomap は同じ ROS_DOMAIN_ID・host network。
- **liboctomap 1.9.7（Ubuntu）は OpenMP なし**（libgomp につながっていない）。点群の挿入は 1 スレッドで動く（`dev_log.md` の 1）。
- ホストの `.bashrc` に `xhost +local:`。RTX 50xx でおかしいときはコンテナの `.bashrc` に `MESA_LOADER_DRIVER_OVERRIDE=zink`（README）。

## よく使うコマンド

コンテナ内の ROS 環境は `~/.bashrc` で読み込まれるので、`docker exec` では `bash -ic` を使う。起動の順は Gazebo → test の推定 → octomap。

```bash
# Gazebo（20261002。localization/CLAUDE.md の「よく使うコマンド」と同じ）。止めるときは pkill -INT -f "ros2 launch connection_wheelchair"
docker exec -d 20261002 bash -ic 'ros2 launch connection_wheelchair connection_wheelchair.launch.py > /tmp/claude_gazebo_launch.log 2>&1'
# 自己位置推定（test）。止めるときは pkill -INT -f "ros2 launch localization_bringup"
docker exec -d test bash -ic 'ros2 launch localization_bringup localization.launch.py env:=gazebo rviz:=false map_path:=/root/ros2_ws/map/SC10_4_0.05.pcd > /tmp/claude_localization_launch.log 2>&1'
# OctoMap（octomap）。引数：env（gazebo）、rviz、throttle（点群を間引く）、log_level（debug で処理時間）
docker exec -d octomap bash -ic 'ros2 launch /root/octomap/config/octomap.launch.py env:=gazebo rviz:=true > /tmp/claude_octomap_launch.log 2>&1'
# 走らせる（test の中から。録画はしない）
docker exec test bash -ic 'python3 /root/ros2_ws/localization_tools/drive/drive_test.py gazebo slalom --yes'
```

- コンテナの中のコマンド：`octomap [env（既定 gazebo）] [rviz（true|false）]`、`octomap_params [env]`（`params.yaml` を `code` で開く）、`reload`。
- **`docker exec ... bash -ic` の中で `ros2 launch ... &` としない。** 長く動かすものは `docker exec -d` で起動し、`pkill -INT -f` で止め、止まったことを `ps` で確かめる。
  rviz2 は SIGINT で止まらないことがあるので、そのときは SIGKILL（`pkill -KILL -x rviz2`）。
- **`timeout` の中で `ros2 topic` などを使うときは `--no-daemon --spin-time 3` を付ける**（`ros2 topic hz` は `--no-daemon` を受け付けない）。
- `test` の `drive gazebo ...`（`run_test.sh`）は推定を自分で起動・停止するので、推定が既に動いていると「localization processes are still running」で止まる。
  推定を別に起動して走らせるときは `drive_test.py` を直接使う（録画はしない。`dev_log.md` の 2）。
- `test` にはユーザーの VS Code がつながっていることがある（`ps` に node・copilot が出る）。止めない。

## OctoMap の性質と注意

- **購読されたトピックだけを作る**。RViz では `/octomap_full` だけを購読し、`/occupied_cells_vis_array`・`/projected_map` は購読しない（重くなる）。
- RViz の OctoMap の表示（octomap_rviz_plugins 2.1.1 の `OccupancyGrid`）はトピックのプロパティ名が **`Topic`**（`Octomap Topic` では購読しない）。
  2D Pose Estimate・2D Goal Pose は外す（押すと `/initialpose` が NDT と EKF に届く）。視点は `base_link` を追う Orbit（距離 25 m）。
- QoS：Gazebo の `/velodyne_points` は RELIABLE、octomap_server の購読は BEST_EFFORT（互換。中継は要らない）。
- **処理の重さ**（Gazebo、slalom、`dev_log.md` の 3）：0.1 m・20 m は点群ごとに更新（挿入 50 ms + 配信 12 ms、CPU 63 %）。0.05 m は 1 コアを使い切り
  （挿入 約 0.25 s + `/octomap_full` 20 MB の配信 約 0.23 s。配信は地図が広がるほど伸びる）、点群の 8 割を捨てる。最大距離 10 m はほとんど効かない。
  0.05 m にするなら `throttle:=true` で 1 Hz（2 Hz は間に合わない）。
- 捨てた点群の量は、MessageFilter のログ（2.5 s に 1 回までの INFO で、出ないこともある）ではなく、`/octomap_full` の数／点群の数で見る。
- `throttle` の実行ファイル（topic_tools 1.1.2）は種類（`messages`）を最初の位置引数で受け取らないと「Throttle type is missing.」で終わる（launch が渡す）。
- 起動時の `Could not open file` の WARN は `octomap_path: ""`（読む地図なし）のため。動作には関係ない。
- 歩行者（gazebo_sfm_plugin）：今の Gazebo の起動コマンドのワールド `SC_10_4.world` には歩行者がいない（`school3F`・`jireiken` にはいるが launch で
  コメントアウト）。跡は光線が通り抜けたときだけ消える（上限から占有でなくなるまで miss 9 回）。実測していない（`dev_log.md` の 3）。
- 測るとき：Gazebo の実時間比は約 0.99。点群は 10.5〜11 Hz で届く（1〜3 ms 違いの組があるため）。周期・遅れは sim time で見る。
