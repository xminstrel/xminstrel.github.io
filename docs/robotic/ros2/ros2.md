[鱼香 ROS](https://fishros.com/d2lros2/#/)

古月居




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



### ros cli

运行节点(常用)  包名，文件名

```
ros2 run <package_name> <executable_name>
```

查看节点列表(常用)：

```
ros2 node list
```

查看节点信息(常用)：

```
ros2 node info <node_name>
```

重映射节点名称

```
ros2 run turtlesim turtlesim_node --ros-args --remap __node:=my_turtle
```

运行节点时设置参数

```
ros2 run example_parameters_rclcpp parameters_basic --ros-args -p rcl_log_level:=10
```




功能包可以理解为存放节点的地方，ROS 2 中功能包根据编译方式的不同分为三种类型。

- ament_python，适用于 python 程序
- cmake，适用于 C++
- ament_cmake，适用于 C++程序,是 cmake 的增强版



#### 功能包获取
安装一般使用

```
sudo apt install ros-<version>-package_name
```

安装获取会自动放置到系统目录，不用再次手动 source。

### rclcpp 编写节点

创建 example_cpp 功能包，使用 ament-cmake 作为编译类型，并为其添加 rclcpp 依赖。

```
cd chapt2_ws/src
ros2 pkg create example_cpp --build-type ament_cmake --dependencies rclcpp
```



- pkg create 是创建包的意思
- --build-type 用来指定该包的编译类型，一共有三个可选项 `ament_python`、`ament_cmake`、`cmake`
- --dependencies 指的是这个功能包的依赖，这里小鱼给了一个 ros 2 的 C++客户端接口 `rclcpp`


### rclpy 编写节点

```
ros2 pkg create example_py --build-type ament_python --dependencies rclpy
```


编写 ROS 2 节点的一般步骤

```
1. 导入库文件
2. 初始化客户端库
3. 新建节点
4. spin循环节点
5. 关闭客户端库
```


### 面向对象编程 oop



### colcon 


### service
