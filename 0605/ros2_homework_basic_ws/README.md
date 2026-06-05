运行指令
colcon build （第一次）
source install/setup.sh
ros2 launch ros2_homework_basic_package turtleeight.launch.py


乌龟的运动消息格式是 Twist

线速度
Twist.linear.x
Twist.linear.y
Twist.linear.z

角速度
Twist.angular.x
Twist.angular.y
Twist.angular.z


Twist.angular.z能控制乌龟的转向

Twist.angular.z > 0 逆时针
Twist.angular.z < 0 顺时针


通过sin函数周期性改变角速度正负，使乌龟运动完一个圆周后改变顺逆时针，保证乌龟的画两个圆是相切的


遇到问题：
头名称不匹配导致传参失败：统一检查修改名称
运动参数对乌龟运动影响和地图大小不明：试运行查看
成员变量相关报错：统一声明和赋值顺序

.yaml：节点参数配置
.launch.py：启动节点列表
.cpp：定义节点类
    创建订阅方
    创建发布方
    创建定时器，绑定回调函数
    节点内函数实现
    int main(int argc, char ** argv)
    {
        rclcpp::init(argc, argv);
        auto node = std::make_shared<”Topic“>();
        rclcpp::spin(node);
        rclcpp::shutdown();
        return 0;
    }

AI解释报错和twist

部分代码沿用模板