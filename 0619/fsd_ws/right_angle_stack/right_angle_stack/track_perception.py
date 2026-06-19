import random

import rclpy
from fsd_common_msgs.msg import Cone, ConeDetections, Map
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node

from .track_model import load_cones_from_sdf
from .utils import quaternion_to_yaw, world_to_body

# 内置锥桶感知：从赛道 SDF 读取锥桶位置，按定位位姿输出局部观测。


DEFAULT_CONES = [
    # 备用的硬编码锥桶列表（world 坐标）
    ('blue', -2.0, -15.0, 0.0), ('yellow', 2.0, -15.0, 0.0),
    ('blue', -2.0, -10.0, 0.0), ('yellow', 2.0, -10.0, 0.0),
    ('blue', -2.0, -5.0, 0.0), ('yellow', 2.0, -5.0, 0.0),
    ('blue', -2.0, 0.0, 0.0), ('yellow', 2.0, 0.0, 0.0),
    ('blue', -1.31, 4.32, 0.0), ('yellow', 2.76, 3.83, 0.0),
    ('blue', 0.68, 8.23, 0.0), ('yellow', 4.93, 7.07, 0.0),
    ('blue', 3.77, 11.32, 0.0), ('yellow', 8.17, 9.24, 0.0),
    ('blue', 7.68, 13.31, 0.0), ('yellow', 12.0, 10.0, 0.0),
    ('blue', 12.0, 14.0, 0.0), ('yellow', 17.0, 10.0, 0.0),
    ('blue', 17.0, 14.0, 0.0), ('yellow', 22.0, 10.0, 0.0),
    ('blue', 22.0, 14.0, 0.0), ('yellow', 27.0, 10.0, 0.0),
    ('blue', 27.0, 14.0, 0.0),
]


class TrackPerception(Node):
    def __init__(self):
        super().__init__('track_perception')

        self.declare_parameter('track_sdf', '')

        # 身前感知距离
        self.declare_parameter('max_range', 18.0)
        # 横向感知距离
        self.declare_parameter('lateral_range', 9.0) 
        # 身后感知距离
        self.declare_parameter('rear_margin', 1.0)

        # 加轻微噪声，尽量还原感知的噪声。
        self.declare_parameter('position_noise_std', 0.05)
        self.declare_parameter('publish_rate', 10.0)

        self.declare_parameter('map_topic', '/perception/cones')
        self.declare_parameter('detections_topic', '/perception/cone_detections')

        self.max_range = float(self.get_parameter('max_range').value)
        self.lateral_range = float(self.get_parameter('lateral_range').value)
        self.rear_margin = float(self.get_parameter('rear_margin').value)
        self.noise_std = float(self.get_parameter('position_noise_std').value)

        # 尝试根据传入的路径加载 SDF 模型。如果路径为空或加载抛出异常，则打印警告并使用 DEFAULT_CONES
        track_sdf = str(self.get_parameter('track_sdf').value)
        if track_sdf:
            try:
                self.cones = load_cones_from_sdf(track_sdf)
            except Exception as exc:
                self.get_logger().warn(f'Failed to load track SDF, using built-in cone list: {exc}')
                self.cones = DEFAULT_CONES
        else:
            self.cones = DEFAULT_CONES

        # 初始化车辆的默认位姿
        self.x = 0.0
        self.y = -15.0
        self.yaw = 1.57079632679

        # 发布按颜色分类的 Map 消息
        self.map_pub = self.create_publisher(Map, self.get_parameter('map_topic').value, 10)
        # 原始检测列表 ConeDetections
        self.det_pub = self.create_publisher(ConeDetections, self.get_parameter('detections_topic').value, 10)
        # 订阅车辆的实时定位话题
        self.create_subscription(PoseStamped, '/localization/pose', self.on_pose, 10)
        self.create_timer(1.0 / float(self.get_parameter('publish_rate').value), self.on_timer)
        self.get_logger().info(f'Track perception publishing {len(self.cones)} known cones in base_link frame.')

    # 收到定位消息时，更新车辆当前的全局坐标和偏航角
    def on_pose(self, msg):
        self.x = msg.pose.position.x
        self.y = msg.pose.position.y
        self.yaw = quaternion_to_yaw(msg.pose.orientation)

    # 创建 Cone 消息，叠加一个高斯噪声，模拟传感器误差，设置位置置信度和颜色置信度
    def make_local_cone(self, color, local_x, local_y, z):
        cone = Cone()
        cone.position.x = local_x + random.gauss(0.0, self.noise_std)
        cone.position.y = local_y + random.gauss(0.0, self.noise_std)
        cone.position.z = z
        cone.color = color
        cone.pose_confidence = 0.9
        cone.color_confidence = 0.98
        return cone

    def on_timer(self):
        stamp = self.get_clock().now().to_msg()
        cone_map = Map()
        cone_map.header.stamp = stamp

        # 设置坐标系为 base_link（车体坐标系），输出相对车辆的坐标
        cone_map.header.frame_id = 'base_link'

        detections = ConeDetections()
        detections.header = cone_map.header

        for color, wx, wy, wz in self.cones:
            # world -> base_link，判断锥桶相对车辆的前后左右
            local_x, local_y = world_to_body(wx - self.x, wy - self.y, self.yaw)

            # 过滤车后方或过远锥桶。
            if local_x < -self.rear_margin or local_x > self.max_range:
                continue
            # 过滤横向距离过大的锥桶
            if abs(local_y) > self.lateral_range:
                continue

            # 生成 Cone 消息
            cone = self.make_local_cone(color, local_x, local_y, wz)
            detections.cone_detections.append(cone)

            # Map 消息按颜色分组；ConeDetections 单一数组
            if color == 'blue':
                cone_map.cone_blue.append(cone)
            elif color == 'yellow':
                cone_map.cone_yellow.append(cone)
            elif color == 'red':
                cone_map.cone_red.append(cone)
            else:
                cone_map.cone_unknown.append(cone)

        self.map_pub.publish(cone_map)
        self.det_pub.publish(detections)


def main(args=None):
    rclpy.init(args=args)
    node = TrackPerception()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
