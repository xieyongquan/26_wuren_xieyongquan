#include <chrono>
#include <functional>
#include <memory>

#include "geometry_msgs/msg/twist.hpp"
#include "rclcpp/rclcpp.hpp"

#define _USE_MATH_DEFINES
#include <cmath>

using namespace std::chrono_literals;

class TopicPublisher : public rclcpp::Node
{
public:
  TopicPublisher()
  : Node("topic_publisher"), 
      //从yaml传入线速度，角速度
      linear_(this->declare_parameter<double>("linear", 0)),
      angular_(this->declare_parameter<double>("angular", 0)),
      //声明t_=0，用于角速度计算
      t_(0.0)
  {
    //创建发布方：向 /turtle1/cmd_vel 发布 Twist 消息
    publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle1/cmd_vel", 10);
    //创建定时器：每 20ms 触发一次回调
    timer_ = this->create_wall_timer(
      20ms, std::bind(&TopicPublisher::publish_circle_command, this));
  }
private:
  void publish_circle_command()
  {
    //组织消息并发布
    geometry_msgs::msg::Twist msg;
    msg.linear.x = linear_; //线速度不变
    msg.linear.y = 0.0;
    msg.linear.z = 0.0;
    msg.angular.x = 0.0;
    msg.angular.y = 0.0;

    //角速度大小不变，运动完一个圆周后改变正负
    if ( sin( angular_ * t_ / 2 ) >= 0 )
        msg.angular.z = angular_ ;
    else
        msg.angular.z = -angular_ ;

    RCLCPP_INFO(
      this->get_logger(),
      "发布运动指令: linear.x=%.2f, angular.z=%.2f",
      msg.linear.x,
      msg.angular.z);

    publisher_->publish(msg);
    
    //t_增加0.02，对应回调周期20ms，乌龟运动完两个圆周（即一个八字）后清零
    t_ += 0.02;
    if ( t_ >= 4 * M_PI / angular_ )
      t_ = 0;

  }

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;

  double linear_;
  double angular_;
  double t_;
};

int main(int argc, char ** argv)
{
  //初始化 ROS2 客户端库，让当前进程能够参与 rclcpp 通信。
  rclcpp::init(argc, argv);

  //定义节点类，并创建发布方节点对象。
  auto node = std::make_shared<TopicPublisher>();

  //调用 spin 函数，并传入节点对象指针，保持节点持续运行并响应定时器。
  rclcpp::spin(node);

  //释放资源：关闭 ROS2 客户端库，结束节点生命周期。
  rclcpp::shutdown();
  return 0;
}