"""走行しながら OctoMap を作って表示する（octomap_server と rviz2）。

起動：ros2 launch /root/octomap/config/octomap.launch.py env:=gazebo rviz:=true（log_level・throttle は省略可）
  env  ：param/<env>/params.yaml を選び、octomap_server と rviz2 の両方に渡す（既定 gazebo）
  rviz ：rviz2 を起動するか（既定 true）
  log_level ：octomap_server のロガーのレベル（既定 info。debug で点群の挿入・地図の配信にかかった時間を出す）
  throttle ：点群を topic_tools の throttle で間引いてから octomap_server に渡すか（既定 false。レートは params.yaml の cloud_throttle）
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node

# ---------- 定数 ----------
CONFIG_DIR = os.path.dirname(os.path.realpath(__file__))   # このファイルの場所（/root/octomap/config）
DEFAULT_ENV = 'gazebo'                                     # 環境（param/<env>/）の既定
DEFAULT_RVIZ = 'true'                                      # rviz2 を起動するかの既定
DEFAULT_LOG_LEVEL = 'info'                                 # octomap_server のロガーのレベルの既定
DEFAULT_THROTTLE = 'false'                                 # 点群を間引くかの既定
PARAM_DIR = 'param'                                        # 環境ごとのパラメータのフォルダ
PARAM_FILE = 'params.yaml'                                 # 環境のパラメータ（octomap_server・rviz2 の節）
RVIZ_CONFIG = os.path.join(CONFIG_DIR, 'rviz', 'octomap.rviz')
CLOUD_TOPIC = '/velodyne_points'                           # octomap_server の cloud_in の付け替え先
THROTTLED_TOPIC = '/velodyne_points_throttle'              # 間引いた点群（throttle:=true のとき cloud_in をこちらにする）
OCTOMAP_PKG = 'octomap_server'
OCTOMAP_EXEC = 'octomap_server_node'
OCTOMAP_NODE = 'octomap_server'                            # params.yaml の節の名前と同じにする
RVIZ_NODE = 'rviz2'                                        # 同上
THROTTLE_NODE = 'cloud_throttle'                           # 同上
THROTTLE_TYPE = 'messages'                                 # 間引き方（メッセージの数。throttle の実行ファイルは最初の引数で受け取る）


def generate_launch_description():
    """launch の記述を返す。入力：launch 引数 env・rviz・log_level・throttle。
    出力：octomap_server と（rviz:=true なら）rviz2、（throttle:=true なら）点群の throttle を起動する LaunchDescription。"""
    env = LaunchConfiguration('env')
    rviz = LaunchConfiguration('rviz')
    log_level = LaunchConfiguration('log_level')
    throttle = LaunchConfiguration('throttle')
    # throttle:=true なら間引いた点群、false なら元の点群を octomap_server に渡す
    cloud_in = PythonExpression([f"'{THROTTLED_TOPIC}' if '", throttle, f"' == 'true' else '{CLOUD_TOPIC}'"])
    params = PathJoinSubstitution([CONFIG_DIR, PARAM_DIR, env, PARAM_FILE])

    return LaunchDescription([
        DeclareLaunchArgument('env', default_value=DEFAULT_ENV,
                              description='環境の名前（param/<env>/params.yaml を使う）'),
        DeclareLaunchArgument('rviz', default_value=DEFAULT_RVIZ,
                              description='rviz2 を起動するか'),
        DeclareLaunchArgument('log_level', default_value=DEFAULT_LOG_LEVEL,
                              description='octomap_server のロガーのレベル（debug で処理時間を出す）'),
        DeclareLaunchArgument('throttle', default_value=DEFAULT_THROTTLE,
                              description='点群を間引いてから octomap_server に渡すか（レートは params.yaml の cloud_throttle）'),
        Node(package='topic_tools', executable='throttle', name=THROTTLE_NODE, arguments=[THROTTLE_TYPE],
             parameters=[params, {'throttle_type': THROTTLE_TYPE, 'input_topic': CLOUD_TOPIC, 'output_topic': THROTTLED_TOPIC}],
             output='screen', condition=IfCondition(throttle)),
        Node(package=OCTOMAP_PKG, executable=OCTOMAP_EXEC, name=OCTOMAP_NODE,
             parameters=[params], remappings=[('cloud_in', cloud_in)], output='screen',
             arguments=['--ros-args', '--log-level', [OCTOMAP_NODE, ':=', log_level]]),
        Node(package='rviz2', executable='rviz2', name=RVIZ_NODE,
             arguments=['-d', RVIZ_CONFIG], parameters=[params], output='screen',
             condition=IfCondition(rviz)),
    ])
