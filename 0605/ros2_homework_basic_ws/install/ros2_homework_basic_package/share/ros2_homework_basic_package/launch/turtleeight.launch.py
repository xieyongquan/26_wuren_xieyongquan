from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    
    yaml_path = PathJoinSubstitution(
        [FindPackageShare('ros2_homework_basic_package'), 'config', 'turtleeight_param.yaml']
    )

    turtlesim_node = Node(
        package="turtlesim",
        executable="turtlesim_node",
        name='turtlesim',
        output="screen"
    )

    turtleeight_node = Node(
        package="ros2_homework_basic_package",
        executable="turtleeight",
        name='turtleeight',
        output="screen",
        parameters=[yaml_path]
    )

    return LaunchDescription([
        turtlesim_node, 
        turtleeight_node
    ])