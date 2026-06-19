import math

import rclpy
from fsd_common_msgs.msg import Cone, ConeDetections, Map
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray

from .utils import body_to_world, color_key, quaternion_to_yaw, set_marker_color

# 把局部锥桶观测合并成 world 坐标系下的地图。


class ConeMapper(Node):
    def __init__(self):
        super().__init__('cone_mapper')

        # sim_perception 和内置兜底感知的话题都可以从 launch 中切换
        self.declare_parameter('perception_map_topic', '/perception/cones')
        self.declare_parameter('perception_detections_topic', '/perception/cone_detections')

        # merge_distance 越大，越容易把两次观测合并为同一个地标
        self.declare_parameter('merge_distance', 0.75)
        self.declare_parameter('world_frame', 'world')
        self.declare_parameter('base_frame', 'base_link')

        # # 获取并缓存这些参数的值
        self.merge_distance = float(self.get_parameter('merge_distance').value)
        self.world_frame = str(self.get_parameter('world_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.pose = None

        # 按颜色分类存储全局锥桶地图
        self.landmarks = {
            'blue': [],
            'yellow': [],
            'red': [],
            'unknown': [],
        }
        # 发布 Map 供规划/控制使用
        self.map_pub = self.create_publisher(Map, '/estimation/slam/map', 10)
        # 发布 MarkerArray 供 RViz 可视化显示
        self.marker_pub = self.create_publisher(MarkerArray, '/visualization/cone_map', 10)

        # 订阅车辆定位话题
        self.create_subscription(PoseStamped, '/localization/pose', self.on_pose, 10)

        # 订阅感知模块发布的 Map
        self.create_subscription(
            Map,
            self.get_parameter('perception_map_topic').value,
            self.on_map_detection,
            10,
        )
        # 订阅感知模块发布的原始锥桶
        self.create_subscription(
            ConeDetections,
            self.get_parameter('perception_detections_topic').value,
            self.on_cone_detections,
            10,
        )

        self.create_timer(0.2, self.publish_outputs)
        self.get_logger().info('Cone mapper started. Local perception is transformed into the world ENU frame.')

    # 位姿回调
    def on_pose(self, msg):
        self.pose = (
            msg.pose.position.x,
            msg.pose.position.y,
            quaternion_to_yaw(msg.pose.orientation),
        )

    # 收到感知的 Map 消息时，分别对蓝、黄、红、未知颜色的锥桶列表进行处理，处理完后立即触发一次发布
    def on_map_detection(self, msg):
        self.process_cones(msg.header.frame_id, msg.cone_blue, 'blue')
        self.process_cones(msg.header.frame_id, msg.cone_yellow, 'yellow')
        self.process_cones(msg.header.frame_id, msg.cone_red, 'red')
        self.process_cones(msg.header.frame_id, msg.cone_unknown, 'unknown')
        self.publish_outputs()

    # 收到原始 Map 消息时，不分颜色统一处理锥桶列表，处理完后立即触发一次发布
    def on_cone_detections(self, msg):
        self.process_cones(msg.header.frame_id, msg.cone_detections, None)
        self.publish_outputs()

    # 锥桶处理函数
    def process_cones(self, frame_id, cones, fallback_color):
        for cone in cones:
            key = color_key(cone.color or fallback_color)
            # 将锥桶从局部坐标系转换到世界坐标系
            transformed = self.to_world(frame_id, cone)
            if transformed is None:
                continue
            # 将该锥桶与世界地图进行匹配融合
            wx, wy = transformed
            self.merge_landmark(key, wx, wy, cone.pose_confidence, cone.color_confidence)

    # 坐标处理函数
    def to_world(self, frame_id, cone):
        frame = (frame_id or self.base_frame).strip('/')
        # 如果感知数据本身就已经在世界坐标系下，直接返回坐标
        if frame in (self.world_frame, 'map'):
            return cone.position.x, cone.position.y
        # 如果还没有收到车辆定位，无法进行坐标转换
        if self.pose is None:
            return None
        # 取出当前车辆位姿，调用工具函数将车体坐标转换为世界坐标
        x, y, yaw = self.pose
        return body_to_world(cone.position.x, cone.position.y, x, y, yaw)

    # 地标融合算法
    def merge_landmark(self, color, x, y, pose_confidence, color_confidence):
        # 最近邻匹配，重复观测用加权平均压噪
        bucket = self.landmarks[color]
        closest = None
        best_distance = float('inf') 
        # 尝试匹配已有锥桶
        for landmark in bucket:
            dist = math.hypot(landmark['x'] - x, landmark['y'] - y)
            if dist < best_distance:
                best_distance = dist
                closest = landmark
        # 全新的锥桶，直接添加到地图中
        if closest is None or best_distance > self.merge_distance:
            bucket.append({
                'x': x,
                'y': y,
                'count': 1,
                'pose_confidence': pose_confidence,
                'color_confidence': color_confidence,
            })
            return
        # 匹配到了已有锥桶，多次观测使用加权滑动平均更新位置
        count = min(closest['count'] + 1, 30)
        alpha = 1.0 / count
        closest['x'] = (1.0 - alpha) * closest['x'] + alpha * x
        closest['y'] = (1.0 - alpha) * closest['y'] + alpha * y
        closest['count'] = count
        # 保存置信度
        closest['pose_confidence'] = max(closest['pose_confidence'], pose_confidence)
        closest['color_confidence'] = max(closest['color_confidence'], color_confidence)

    # msg 转换函数
    def make_cone(self, color, landmark):
        cone = Cone()
        cone.position.x = landmark['x']
        cone.position.y = landmark['y']
        cone.position.z = 0.0
        cone.color = color
        cone.pose_confidence = float(landmark['pose_confidence'])
        cone.color_confidence = float(landmark['color_confidence'])
        return cone

    def publish_outputs(self):
        # 发布结构化地图消息
        stamp = self.get_clock().now().to_msg()
        msg = Map()
        msg.header.stamp = stamp
        msg.header.frame_id = self.world_frame
        msg.cone_blue = [self.make_cone('blue', item) for item in self.landmarks['blue']]
        msg.cone_yellow = [self.make_cone('yellow', item) for item in self.landmarks['yellow']]
        msg.cone_red = [self.make_cone('red', item) for item in self.landmarks['red']]
        msg.cone_unknown = [self.make_cone('unknown', item) for item in self.landmarks['unknown']]
        self.map_pub.publish(msg)

        # 发布可视化锥桶地图
        markers = MarkerArray()
        clear = Marker()
        clear.header = msg.header
        clear.action = Marker.DELETEALL
        markers.markers.append(clear)

        marker_id = 0
        for color, bucket in self.landmarks.items():
            for landmark in bucket:
                marker = Marker()
                marker.header = msg.header
                marker.ns = f'{color}_cones'
                marker.id = marker_id
                marker_id += 1
                marker.type = Marker.CYLINDER
                marker.action = Marker.ADD
                marker.pose.position.x = landmark['x']
                marker.pose.position.y = landmark['y']
                marker.pose.position.z = 0.28
                marker.pose.orientation.w = 1.0
                marker.scale.x = 0.35
                marker.scale.y = 0.35
                marker.scale.z = 0.56
                set_marker_color(marker, color)
                markers.markers.append(marker)
        self.marker_pub.publish(markers)


def main(args=None):
    rclpy.init(args=args)
    node = ConeMapper()
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
