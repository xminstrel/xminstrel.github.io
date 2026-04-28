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

大家可以手写一下这个代码，感受一下。现在小鱼来讲一讲这条命令的含义和参数。

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



## [2.Colcon构建进阶](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_2colcon%e6%9e%84%e5%bb%ba%e8%bf%9b%e9%98%b6)

我们平时用的最多的场景是编译功能包，所以这里小鱼重点介绍 build 时候的一些参数。

### [2.1 build参数](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_21-build%e5%8f%82%e6%95%b0)

#### [2.1.0 构建指令](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_210-%e6%9e%84%e5%bb%ba%e6%8c%87%e4%bb%a4)

- `--packages-select` ，仅生成单个包（或选定的包）。
- `--packages-up-to`，构建选定的包，包括其依赖项。
- `--packages-above`，整个工作区，然后对其中一个包进行了更改。此指令将重构此包以及（递归地）依赖于此包的所有包。

#### [2.1.1.指定构建后安装的目录](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_211%e6%8c%87%e5%ae%9a%e6%9e%84%e5%bb%ba%e5%90%8e%e5%ae%89%e8%a3%85%e7%9a%84%e7%9b%ae%e5%bd%95)

可以通过 `--build-base` 参数和 `--install-base`，指定构建目录和安装目录。

#### [2.1.2.合并构建目录](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_212%e5%90%88%e5%b9%b6%e6%9e%84%e5%bb%ba%e7%9b%ae%e5%bd%95)

`--merge-install`，使用 作为所有软件包的安装前缀，而不是安装基中的软件包特定子目录。--install-base

如果没有此选项，每个包都将提供自己的环境变量路径，从而导致非常长的环境变量值。

使用此选项时，添加到环境变量的大多数路径将相同，从而导致环境变量值更短。

#### [2.1.3.符号链接安装](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_213%e7%ac%a6%e5%8f%b7%e9%93%be%e6%8e%a5%e5%ae%89%e8%a3%85)

启用 `--symlink-install` 后将不会把文拷贝到 install 目录，而是通过创建符号链接的方式。

#### [2.1.4.错误时继续安装](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_214%e9%94%99%e8%af%af%e6%97%b6%e7%bb%a7%e7%bb%ad%e5%ae%89%e8%a3%85)

启用 `--continue-on-error`，当发生错误的时候继续进行编译。

#### [2.1.5 CMake参数](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_215-cmake%e5%8f%82%e6%95%b0)

`--cmake-args`，将任意参数传递给 CMake。与其他选项匹配的参数必须以空格为前缀。

#### [2.1.6 控制构建线程](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_216-%e6%8e%a7%e5%88%b6%e6%9e%84%e5%bb%ba%e7%ba%bf%e7%a8%8b)

- `--executor EXECUTOR`，用于处理所有作业的执行程序。默认值是根据所有可用执行程序扩展的优先级选择的。要查看完整列表，请调用 `colcon extensions colcon_core.executor --verbose`。
    
    - `sequential` [`colcon-core`]
        
        一次处理一个包。
        
    - `parallel` [`colcon-parallel-executor`]
        
        处理多个作业**平行**.
        
- --parallel-workers NUMBER
    
    - 要并行处理的最大作业数。默认值为 [os.cpu_count()](https://docs.python.org/3/library/os.html#os.cpu_count) 给出的逻辑 CPU 内核数。

#### [2.1.7 开启构建日志](https://fishros.com/d2lros2/#/humble/chapt2/advanced/3.Colcon%E4%BD%BF%E7%94%A8%E8%BF%9B%E9%98%B6?id=_217-%e5%bc%80%e5%90%af%e6%9e%84%e5%bb%ba%e6%97%a5%e5%bf%97)

使用 `--log-level` 可以设置日志级别，比如 `--log-level info`。




## [3.ROS2服务常用命令](https://fishros.com/d2lros2/#/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8?id=_3ros2%e6%9c%8d%e5%8a%a1%e5%b8%b8%e7%94%a8%e5%91%bd%e4%bb%a4)

ROS 2 的命令行工具，小鱼觉得还是非常值得一学的，毕竟确实很实用（装 X），之前已经给大家讲过了关于节点、话题、接口相关的命令了，现在小鱼说一下关于服务的那些命令行。

### [3.1查看服务列表](https://fishros.com/d2lros2/#/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8?id=_31%e6%9f%a5%e7%9c%8b%e6%9c%8d%e5%8a%a1%e5%88%97%e8%a1%a8)

```
ros2 service list
```

![image-20210810115216800](https://fishros.com/d2lros2/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8/imgs/image-20210810115216800.png)

### [3.2手动调用服务](https://fishros.com/d2lros2/#/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8?id=_32%e6%89%8b%e5%8a%a8%e8%b0%83%e7%94%a8%e6%9c%8d%e5%8a%a1)

```
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 5,b: 10}"
```

![image-20210810115316799](https://fishros.com/d2lros2/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8/imgs/image-20210810115316799.png)

如果不写参数值调用会怎么样？比如下面这种，大家可以尝试下。

```
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts
```

### [3.3 查看服务接口类型](https://fishros.com/d2lros2/#/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8?id=_33-%e6%9f%a5%e7%9c%8b%e6%9c%8d%e5%8a%a1%e6%8e%a5%e5%8f%a3%e7%b1%bb%e5%9e%8b)

```
ros2 service type /add_two_ints
```

![image-20210810115428267|397](https://fishros.com/d2lros2/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8/imgs/image-20210810115428267.png)

### [3.4查找使用某一接口的服务](https://fishros.com/d2lros2/#/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8?id=_34%e6%9f%a5%e6%89%be%e4%bd%bf%e7%94%a8%e6%9f%90%e4%b8%80%e6%8e%a5%e5%8f%a3%e7%9a%84%e6%9c%8d%e5%8a%a1)

这个命令看起来和 3.3 刚好相反。

```
ros2 service find example_interfaces/srv/AddTwoInts
```
![image-20210810115552147](https://fishros.com/d2lros2/humble/chapt3/get_started/4.ROS2%E6%9C%8D%E5%8A%A1%E5%85%A5%E9%97%A8/imgs/image-20210810115552147.png)