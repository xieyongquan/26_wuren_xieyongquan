#include <rclcpp/rclcpp.hpp>
#include <fsd_common_msgs/msg/map.hpp>
#include <visualization_msgs/msg/marker_array.hpp>
#include <visualization_msgs/msg/marker.hpp>

using namespace std::chrono_literals;

class MarkerPublisher : public rclcpp::Node
{
public:
    MarkerPublisher() : Node("cone_marker_pub")
    {
		// 创建订阅方：监听 /estimation/slam/map 的 Map 消息
    	map_sub_ = this->create_subscription<fsd_common_msgs::msg::Map>(
      		"/estimation/slam/map",
      		10,
      		std::bind(&MarkerPublisher::receiveMap, this, std::placeholders::_1)
		);

        // 创建 Marker 发布器
		marker_pub_ = this->create_publisher<visualization_msgs::msg::MarkerArray>("visualization_marker", 10);

		// 定时发布，每 500ms 触发一次回调
		timer_ = this->create_wall_timer(500ms, std::bind(&MarkerPublisher::publishMarker, this));
    }

private:

    // 创建 map 的指针
    fsd_common_msgs::msg::Map::SharedPtr map_{nullptr};
   
    // 接收订阅的 map
    void receiveMap(const fsd_common_msgs::msg::Map::SharedPtr map)
    {
        map_ = map;
    }
    
    void publishMarker()
	{
        if (!map_)
            return;

        int id_ = 0;
        visualization_msgs::msg::Marker marker;
        visualization_msgs::msg::MarkerArray marker_arr;
        
        // 设置坐标系
        marker.header.frame_id = map_->header.frame_id;
        marker.header.stamp = map_->header.stamp;

        // 设置命名空间
        marker.ns = "basic_shapes";

        // 设置类型
        marker.type = visualization_msgs::msg::Marker::SPHERE;

        // 设置动作
        marker.action = visualization_msgs::msg::Marker::ADD;

        // 设置姿态
        marker.pose.orientation.x = 0.0;
        marker.pose.orientation.y = 0.0;
        marker.pose.orientation.z = 0.5;
        marker.pose.orientation.w = 1.0;

        // 设置尺寸
        marker.scale.x = 0.5;
        marker.scale.y = 0.5;
        marker.scale.z = 0.5;

        // 设置alpha
        marker.color.a = 1.0f;

        // 生命周期
        marker.lifetime = rclcpp::Duration::from_seconds(0.0);
        
        // 遍历 map 内一种颜色的锥桶
        for (auto &cone : map_->cone_yellow)
        {
            // 设置ID
            marker.id = id_++;

            // 设置位置
            marker.pose.position.x = cone.position.x;
            marker.pose.position.y = cone.position.y;
            marker.pose.position.z = cone.position.z;

            // 设置颜色
            marker.color.r = 1.0f;
            marker.color.g = 1.0f;
            marker.color.b = 0.0f;
            
            // 存入marker_arr
            marker_arr.markers.push_back(marker);
        }

        for (auto &cone : map_->cone_blue)
        {
            marker.id = id_++;
            
            marker.pose.position.x = cone.position.x;
            marker.pose.position.y = cone.position.y;
            marker.pose.position.z = cone.position.z;

            marker.color.r = 0.0f;
            marker.color.g = 0.0f;
            marker.color.b = 1.0f;

            marker_arr.markers.push_back(marker);
        }

        for (auto &cone : map_->cone_red)
        {
            marker.id = id_++;

            marker.pose.position.x = cone.position.x;
            marker.pose.position.y = cone.position.y;
            marker.pose.position.z = cone.position.z;

            marker.color.r = 1.0f;
            marker.color.g = 0.0f;
            marker.color.b = 0.0f;

            marker_arr.markers.push_back(marker);
        }
        
        for (auto &cone : map_->cone_unknown)
        {
            marker.id = id_++;

            marker.pose.position.x = cone.position.x;
            marker.pose.position.y = cone.position.y;
            marker.pose.position.z = cone.position.z;

            marker.color.r = 1.0f;
            marker.color.g = 1.0f;
            marker.color.b = 1.0f;

            marker_arr.markers.push_back(marker);
        }

		// 发布 Marker
		marker_pub_->publish(marker_arr);
	}

    rclcpp::Subscription<fsd_common_msgs::msg::Map>::SharedPtr map_sub_;
	rclcpp::Publisher<visualization_msgs::msg::MarkerArray>::SharedPtr marker_pub_;
	rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv)
{
	rclcpp::init(argc, argv);
	rclcpp::spin(std::make_shared<MarkerPublisher>());
	rclcpp::shutdown();
	return 0;
}