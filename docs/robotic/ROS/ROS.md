鱼香 ROS

古月居


指令 `source ~/.bashrc`
在 home/xmins 中指令
`cd ~`

rm -r 删除目录和子文件

g++编译 ros 节点


cmake 编译

文件名 ：CMakeLists.txt


### cmake 依赖查找
camke步骤：
CMakeLists.txt 里面写三步

 `find_package(rclcpp REQUIRED)`

**找依赖**

`add_executable(first_node first_ros2_node.cpp)`

**定义要生成的程序**

 `target_link_libraries(first_node rclcpp::rclcpp)`

**把程序和依赖库连起来**

``` c++
cmake_minimum_required(VERSION 3.22)

project(first_node)

  

find_package(rclcpp REQUIRED)

add_executable(first_node first_ros2_node.cpp)

target_link_libraries(first_node rclcpp::rclcpp)
```


### python 依赖查找

