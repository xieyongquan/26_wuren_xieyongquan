import math

import rclpy
from fsd_common_msgs.msg import Map
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray

from .utils import yaw_to_quaternion

# 为直角弯任务生成中心线。


class RightAnglePlanner(Node):
    def __init__(self):
        super().__init__('right_angle_planner')

        # 优先使用锥桶地图，允许使用兜底
        self.declare_parameter('prefer_cone_map', True)
        self.declare_parameter('fallback_path', True)

        # 声明直角弯的几何参数
        self.declare_parameter('turn_center_x', 12.0)
        self.declare_parameter('turn_center_y', 0.0)
        self.declare_parameter('turn_radius', 12.0)

        # 声明锥桶配对的最大距离阈值，路径点的插值步长
        self.declare_parameter('pair_distance_max', 6.2)
        self.declare_parameter('path_step', 0.8)

        self.prefer_cone_map = bool(self.get_parameter('prefer_cone_map').value)
        self.use_fallback = bool(self.get_parameter('fallback_path').value)
        self.center_x = float(self.get_parameter('turn_center_x').value)
        self.center_y = float(self.get_parameter('turn_center_y').value)
        self.radius = float(self.get_parameter('turn_radius').value)
        self.pair_distance_max = float(self.get_parameter('pair_distance_max').value)
        self.path_step = float(self.get_parameter('path_step').value)

        self.latest_map = None
        self.current_pose = None
        # 发布 Path 供下游控制使用
        self.path_pub = self.create_publisher(Path, '/planning/centerline', 10)
        #发布 MarkerArray 供 RViz 可视化
        self.marker_pub = self.create_publisher(MarkerArray, '/visualization/planning', 10)
        # 订阅全局锥桶地图
        self.create_subscription(Map, '/estimation/slam/map', self.on_map, 10)
        # 订阅车辆定位话题
        self.create_subscription(PoseStamped, '/localization/pose', self.on_pose, 10)
        self.create_timer(0.1, self.on_timer)
        self.get_logger().info('Right-angle centerline planner started.')

    def on_map(self, msg):
        self.latest_map = msg

    def on_pose(self, msg):
        self.current_pose = msg

    def track_progress(self, point):
        x, y = point
        # 将无序的锥桶中点按行驶顺序排列
        if y <= 0.2 and x < 3.0:
            return y + 15.0
        # 计算该点相对于转弯圆心的极角
        theta = math.atan2(y - self.center_y, x - self.center_x)
        # 如果点在转弯段，将角度限制在 [pi/2, pi] 之间，通过弧长公式 (pi - theta) * R 计算进度
        if x <= self.center_x + 1.0 and y >= -0.5:
            theta = min(math.pi, max(math.pi / 2.0, theta))
            return 15.0 + (math.pi - theta) * self.radius
        # 如果点在出弯后的直道段，进度 = 进弯直道(15) + 转弯弧长(0.5*pi*R) + 出弯直道距离(x - center_x)
        return 15.0 + 0.5 * math.pi * self.radius + max(0.0, x - self.center_x)

    def analytic_path(self):
        # 解析 fallback，根据原始数据计算，便于地图不完整时继续跑通任务
        points = []
        y = -15.0
        while y <= 0.0:
            points.append((0.0, y))
            y += self.path_step

        theta = math.pi
        theta_end = math.pi / 2.0
        dtheta = self.path_step / max(self.radius, 0.1)
        while theta >= theta_end:
            x = self.center_x + self.radius * math.cos(theta)
            y = self.center_y + self.radius * math.sin(theta)
            points.append((x, y))
            theta -= dtheta

        x = self.center_x
        while x <= 32.0:
            points.append((x, self.center_y + self.radius))
            x += self.path_step
        return points

    def cone_centerline(self):
        if self.latest_map is None:
            return []
        # 提取蓝、黄锥桶坐标，如果某一种颜色少于3个，则无法构成有效路径
        blue = [(c.position.x, c.position.y) for c in self.latest_map.cone_blue]
        yellow = [(c.position.x, c.position.y) for c in self.latest_map.cone_yellow]
        if len(blue) < 3 or len(yellow) < 3:
            return []

        # 遍历每个蓝锥，在未配对的黄锥中找距离最近的，如果最近距离小于阈值(6.2m)，则认为它们是一对，取两者的中点作为中心线点
        used_yellow = set()
        midpoints = []
        for bx, by in blue:
            best_index = None
            best_dist = float('inf')
            for index, (yx, yy) in enumerate(yellow):
                if index in used_yellow:
                    continue
                dist = math.hypot(bx - yx, by - yy)
                if dist < best_dist:
                    best_dist = dist
                    best_index = index
            if best_index is None or best_dist > self.pair_distance_max:
                continue
            used_yellow.add(best_index)
            yx, yy = yellow[best_index]
            midpoints.append(((bx + yx) * 0.5, (by + yy) * 0.5))

        # 将得到的中点按照 track_progress 计算的行驶进度进行排序
        midpoints = sorted(midpoints, key=self.track_progress)
        if len(midpoints) < 5:
            return []
        return self.densify(midpoints)

    def densify(self, points):
        # 使用线性插值公式，在两点之间均匀地生成新的路径点，使路径更平滑
        if not points:
            return []
        dense = [points[0]]
        for start, end in zip(points, points[1:]):
            sx, sy = start
            ex, ey = end
            dist = math.hypot(ex - sx, ey - sy)
            steps = max(1, int(dist / self.path_step))
            for i in range(1, steps + 1):
                ratio = i / steps
                dense.append((sx + ratio * (ex - sx), sy + ratio * (ey - sy)))
        return dense

    def choose_path(self):
        cone_path = self.cone_centerline() if self.prefer_cone_map else []
        # 如果优先使用锥桶地图，且生成的路径点 >= 8 个，则采用锥桶路径
        if len(cone_path) >= 8:
            return cone_path, 'cone_map'
        # 如果锥桶路径不可用，且允许 fallback，则返回解析路径
        if self.use_fallback:
            return self.analytic_path(), 'analytic'
        return [], 'none'

    def on_timer(self):
        # 创建 Path 消息
        points, source = self.choose_path()
        if not points:
            return
        stamp = self.get_clock().now().to_msg()
        path = Path()
        path.header.stamp = stamp
        path.header.frame_id = 'world'
    
        for index, (x, y) in enumerate(points):
            pose = PoseStamped()
            pose.header = path.header
            pose.pose.position.x = x
            pose.pose.position.y = y
            # 计算当前点的朝向，优先用下一个点计算前向差分
            if index + 1 < len(points):
                nx, ny = points[index + 1]
                yaw = math.atan2(ny - y, nx - x)
            elif index > 0:
                px, py = points[index - 1]
                yaw = math.atan2(y - py, x - px)
            else:
                yaw = 0.0
            pose.pose.orientation = yaw_to_quaternion(yaw)
            path.poses.append(pose)
        self.path_pub.publish(path)
        self.publish_markers(path.header, points, source)

    def publish_markers(self, header, points, source):
        # 可视化发布
        markers = MarkerArray()
        clear = Marker()
        clear.header = header
        clear.action = Marker.DELETEALL
        markers.markers.append(clear)

        line = Marker()
        line.header = header
        line.ns = 'centerline'
        line.id = 1
        line.type = Marker.LINE_STRIP
        line.action = Marker.ADD
        line.scale.x = 0.12
        line.color.a = 1.0
        if source == 'cone_map':
            line.color.r = 0.0
            line.color.g = 0.9
            line.color.b = 0.35
        else:
            line.color.r = 1.0
            line.color.g = 1.0
            line.color.b = 1.0
        for x, y in points:
            line.points.append(Point(x=x, y=y, z=0.05))
        markers.markers.append(line)
        self.marker_pub.publish(markers)


def main(args=None):
    rclpy.init(args=args)
    node = RightAnglePlanner()
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
