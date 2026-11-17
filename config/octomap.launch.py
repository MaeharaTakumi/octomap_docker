"""走行しながら OctoMap を作って表示する（octomap_server と rviz2）。

起動：ros2 launch /root/octomap/config/octomap.launch.py env:=gazebo rviz:=true
  env  ：param/<env>/params.yaml を選び、octomap_server と rviz2 の両方に渡す（既定 gazebo）
  rviz ：rviz2 を起動するか（既定 true）
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

# ---------- 定数 ----------
CONFIG_DIR = os.path.dirname(os.path.realpath(__file__))   # このファイルの場所（/root/octomap/config）
DEFAULT_ENV = 'gazebo'                                     # 環境（param/<env>/）の既定
DEFAULT_RVIZ = 'true'                                      # rviz2 を起動するかの既定
PARAM_DIR = 'param'                                        # 環境ごとのパラメータのフォルダ
PARAM_FILE = 'params.yaml'                                 # 環境のパラメータ（octomap_server・rviz2 の節）
RVIZ_CONFIG = os.path.join(CONFIG_DIR, 'rviz', 'octomap.rviz')
CLOUD_TOPIC = '/velodyne_points'                           # octomap_server の cloud_in の付け替え先
OCTOMAP_PKG = 'octomap_server'
OCTOMAP_EXEC = 'octomap_server_node'
OCTOMAP_NODE = 'octomap_server'                            # params.yaml の節の名前と同じにする
RVIZ_NODE = 'rviz2'                                        # 同上


def generate_launch_description():
    """launch の記述を返す。入力：launch 引数 env・rviz。出力：octomap_server と（rviz:=true なら）rviz2 を起動する LaunchDescription。"""
    env = LaunchConfiguration('env')
    rviz = LaunchConfiguration('rviz')
    params = PathJoinSubstitution([CONFIG_DIR, PARAM_DIR, env, PARAM_FILE])

    return LaunchDescription([
        DeclareLaunchArgument('env', default_value=DEFAULT_ENV,
                              description='環境の名前（param/<env>/params.yaml を使う）'),
        DeclareLaunchArgument('rviz', default_value=DEFAULT_RVIZ,
                              description='rviz2 を起動するか'),
        Node(package=OCTOMAP_PKG, executable=OCTOMAP_EXEC, name=OCTOMAP_NODE,
             parameters=[params], remappings=[('cloud_in', CLOUD_TOPIC)], output='screen'),
        Node(package='rviz2', executable='rviz2', name=RVIZ_NODE,
             arguments=['-d', RVIZ_CONFIG], parameters=[params], output='screen',
             condition=IfCondition(rviz)),
    ])
