运行指令

第一个终端
colcon build
source install/setup.sh
ros2 run cone_map_visualize cone_map_visualize

第二个终端
source install/setup.sh
ros2 bag play ./map_to_visualize
(bag提前播放完会导致无结果，试ros2 bag play ./map_to_visualize --loop)

第三个终端
source install/setup.sh
rviz2

rviz可视化界面
左下角add
上方by topic
中间markerarray
下方ok
左侧global option:fixer frame 将map改为world


获取包中地图的坐标系

打开终端
source install/setup.sh
ros2 bag play ./map_to_visualize
ros2 topic echo /estimation/slam/map --field header.frame_id


和rviz中默认的map坐标系不符
rviz可视化界面左侧global option:fixer frame 将map改为包中地图的坐标系


遇到问题
Segmentation fault：没判空，map_ == nullptr 直接 map_->xxx 空指针解引用，加入 
    if (!map_)
        return;
定时器回调必须使用无参函数
使用auto自动识别变量格式
指针，引用使用不当
部分msg不认识

AI解释报错和header,position

部分代码沿用模板
