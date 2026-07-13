# ROS 2 + PyTorch 暑假项目式学习计划

> **周期：8 周**  
> **强度：每周 5 天学习 + 1 天整理，约 15～17 小时/周**  
> **总投入：约 120～136 小时**  
> **最终项目：基于 ROS 2、Gazebo、TurtleBot 3 和 PyTorch 的视觉感知避障机器人**

---

## 1. 学习目标

暑假结束时，完成以下能力闭环：

```text
摄像头/图像
    ↓
PyTorch 模型推理
    ↓
ROS2 发布识别结果
    ↓
决策节点融合视觉与激光雷达信息
    ↓
发布速度指令
    ↓
Gazebo 仿真小车运动
```

最终项目至少实现：

-  在 Gazebo 中启动 TurtleBot 3 或其他差速小车
    
-  使用 ROS 2 控制小车前进、后退和转弯
    
-  订阅激光雷达 `/scan`
    
-  实现基础避障
    
-  使用 PyTorch 训练图像分类模型
    
-  模型识别 `left`、`right`、`forward`、`stop`
    
-  将模型推理封装成 ROS 2 节点
    
-  融合视觉命令和雷达安全信息
    
-  使用一个 launch 文件启动整个系统
    
-  编写完整 README 和项目说明
    
-  可选：完成 SLAM 建图和 Nav 2 导航
    

---

## 2. 技术栈

|层级|技术|
|---|---|
|编程语言|Python|
|深度学习|PyTorch、Torchvision|
|图像处理|OpenCV|
|机器人中间件|ROS 2 Jazzy|
|机器人仿真|Gazebo Harmonic|
|仿真机器人|TurtleBot 3|
|可视化|RViz|
|导航|SLAM Toolbox、Nav 2|
|工程工具|Git、GitHub、VS Code、Linux|
|数据处理|NumPy、Matplotlib|

ROS 2 官方教程建议初学者按照顺序完成，因为节点、话题、服务、Action、参数和 launch 等内容前后关联。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials.html?utm_source=chatgpt.com "Tutorials — ROS 2 Documentation: Jazzy documentation"))

对于 Ubuntu 24.04 和 ROS 2 Jazzy，Gazebo 官方推荐使用 Gazebo Harmonic，这是官方测试和支持的组合。([Gazebo](https://gazebosim.org/docs/harmonic/getstarted/ "Getting Started with Gazebo? — Gazebo harmonic documentation"))

---

## 3. 环境安排

### 3.1 推荐设备分工

| 设备                         | 主要任务                     |
| -------------------------- | ------------------------ |
| Mac                        | PyTorch 练习、数据集整理、写代码、写笔记 |
| Windows + WSL Ubuntu 24.04 | ROS 2、Gazebo、RViz、最终项目整合 |
| GitHub                     | 同步代码、保存每周成果              |

### 3.2 环境原则

建议把环境分成两部分：

```text
PyTorch实验环境
├── 独立Python虚拟环境
├── torch
├── torchvision
├── opencv-python
├── numpy
└── matplotlib

ROS2项目环境
├── Ubuntu 24.04
├── ROS2 Jazzy
├── Gazebo Harmonic
├── TurtleBot3
└── Nav2
```

PyTorch 基础可以先在 Mac、Jupyter 或 Colab 中完成。

最终将 PyTorch 模型接入 ROS 2 时，建议把模型推理节点放到 WSL Ubuntu 中运行，避免跨设备传输图像和 ROS 2 网络配置带来的额外问题。

---

## 4. 时间安排

### 4.1 标准学习节奏

每周安排：

|日期|时间|内容|
|---|--:|---|
|周一|3 小时|新知识学习|
|周二|3 小时|跟教程实现|
|周三|3 小时|ROS 2 或 PyTorch 专项|
|周四|3 小时|项目开发|
|周五|3 小时|项目开发与排错|
|周六|2 小时|整理笔记、README、Git 提交|
|周日|休息|不安排强制任务|

每周约：

```text
3小时 × 5天 + 2小时 = 17小时
```

八周约：

```text
17小时 × 8周 = 136小时
```

### 4.2 每天 3 小时模板

```text
00:00—00:30  阅读教程，理解概念
00:30—01:30  跟着教程敲代码
01:30—02:30  脱离教程完成自己的功能
02:30—02:50  排错和记录问题
02:50—03:00  Git commit
```

每天至少留下一个可验证成果，例如：

```text
今天成功发布了一个ROS2 Topic
今天训练循环成功运行
今天Gazebo中的机器人动起来了
今天模型能输出一张图片的预测类别
```

---

# 5. 八周详细计划

---

## 第 1 周：PyTorch Tensor 与 ROS 2 系统观察

### 本周目标

- 认识 PyTorch Tensor
    
- 能进行基本张量运算
    
- 熟悉 ROS 2 命令行
    
- 理解节点、话题和消息
    
- 建立 GitHub 项目仓库
    

### 时间分配

|内容|时间|
|---|--:|
|PyTorch|7 小时|
|ROS 2|6 小时|
|Git 与整理|4 小时|

### Day 1：项目初始化

学习内容：

- 创建 GitHub 仓库
    
- 建立项目目录
    
- 配置 Python 虚拟环境
    
- 检查 ROS 2 Jazzy 环境
    

建议目录：

```text
ros2-pytorch-robot/
├── ml/
│   ├── notebooks/
│   ├── data/
│   ├── models/
│   └── scripts/
├── ros2_ws/
│   └── src/
├── docs/
├── README.md
└── .gitignore
```

完成标准：

-  仓库创建成功
    
-  Mac 或 WSL 能提交代码
    
-  `import torch` 成功
    
-  `ros2 --help` 成功
    

---

### Day 2：Tensor 基础

学习：

- 标量、向量、矩阵和张量
    
- `shape`
    
- `dtype`
    
- 索引和切片
    
- 张量加减乘除
    
- `reshape`
    
- `mean`、`max`、`min`
    
- NumPy 与 Tensor 转换
    

PyTorch 官方将 Tensor 定义为用于表示模型输入、输出及参数的数据结构，并说明 Tensor 与 NumPy 数组相似，但可以运行在硬件加速设备上。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html?utm_source=chatgpt.com "Tensors — PyTorch Tutorials 2.13.0+cu 130 documentation"))

练习：

```python
import torch

distances = torch.tensor([0.8, 0.6, 0.4, 0.2])

print(distances.shape)
print(distances.mean())
print(distances.min())

danger = distances < 0.3
print(danger)
```

完成标准：

-  能解释 `shape`
    
-  能创建二维 Tensor
    
-  能使用布尔条件筛选数据
    
-  能在 Tensor 和 NumPy 间转换
    

---

### Day 3：ROS 2 命令行基础

学习：

```bash
ros2 node list
ros2 node info
ros2 topic list
ros2 topic echo
ros2 topic info
ros2 interface show
```

使用 turtlesim 观察：

```text
/turtle1/cmd_vel
/turtle1/pose
```

重点理解：

```text
Node      = 一个功能模块
Topic     = 持续传输数据的通道
Message   = Topic上传输的数据格式
Publisher = 发送消息
Subscriber = 接收消息
```

ROS 2 官方的 CLI 入门部分包含环境配置、turtlesim、节点、话题、服务、参数、Action、日志、launch 和 rosbag。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html?utm_source=chatgpt.com "Beginner: CLI tools - Jazzy documentation"))

---

### Day 4：PyTorch 设备与批量数据

学习：

- CPU 设备
    
- Apple Silicon 上的 MPS 概念
    
- batch 概念
    
- 二维 Tensor
    
- 广播机制
    
- 随机数和随机种子
    

练习项目：

> 使用 Tensor 模拟 20 个激光雷达距离值，并将其分成安全、减速和危险三类。

规则：

```text
distance > 0.6      → safe
0.3 < distance ≤ 0.6 → slow
distance ≤ 0.3      → danger
```

---

### Day 5：ROS 2 服务、参数与 Action 观察

学习：

```bash
ros2 service list
ros2 service type
ros2 service call

ros2 param list
ros2 param get
ros2 param set

ros2 action list
ros2 action info
```

不要求写代码，只需要知道三种通信模式：

|模式|适用场景|
|---|---|
|Topic|摄像头、雷达、速度等连续数据|
|Service|一次请求和一次响应|
|Action|导航、机械臂运动等耗时任务|

---

### Day 6：整理与复盘

提交：

```text
week01/
├── tensor_basics.py
├── fake_lidar_tensor.py
└── notes.md
```

本周验收：

-  能用 Tensor 处理距离数据
    
-  能查看 ROS 2 节点和 Topic
    
-  能解释 Topic、Service 和 Action 的区别
    
-  至少完成 3 次 Git commit
    

### 本周资源

- PyTorch Learn the Basics：完整覆盖 Tensor、Dataset、模型、自动求导、优化和模型保存。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/basics/intro.html?utm_source=chatgpt.com "Learn the Basics — PyTorch Tutorials 2.13.0+cu 130 ..."))
    
- ROS 2 Jazzy 官方教程。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials.html?utm_source=chatgpt.com "Tutorials — ROS 2 Documentation: Jazzy documentation"))
    
- ROS 2 Beginner CLI Tools。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html?utm_source=chatgpt.com "Beginner: CLI tools - Jazzy documentation"))
    

---

## 第 2 周：PyTorch 训练流程与 ROS 2 发布订阅

### 本周目标

- 理解一个神经网络如何训练
    
- 会定义简单的 `nn.Module`
    
- 会写 ROS 2 Python Publisher 和 Subscriber
    
- 完成第一个 ROS 2 小项目
    

### 时间分配

|内容|时间|
|---|--:|
|PyTorch|8 小时|
|ROS 2|7 小时|
|整理|2 小时|

---

### Day 1：神经网络结构

学习：

- `nn.Module`
    
- `__init__()`
    
- `forward()`
    
- `nn.Linear`
    
- 输入维度和输出维度
    
- logits
    

简单模型：

```python
import torch
from torch import nn


class DistanceClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(1, 8),
            nn.ReLU(),
            nn.Linear(8, 3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)
```

---

### Day 2：Loss 和 Optimizer

学习：

- 预测值和真实标签
    
- `CrossEntropyLoss`
    
- 学习率
    
- SGD 和 Adam
    
- 梯度清零
    
- 反向传播
    
- 参数更新
    

训练循环：

```text
读取一个batch
→ model(x)
→ 计算loss
→ optimizer.zero_grad()
→ loss.backward()
→ optimizer.step()
```

PyTorch 官方优化教程将训练过程拆分为梯度清零、反向传播和优化器更新等步骤。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html?utm_source=chatgpt.com "Optimizing Model Parameters — PyTorch Tutorials 2.13.0+ ..."))

---

### Day 3：创建 ROS 2 Python 包

学习：

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

ros2 pkg create \
  --build-type ament_python \
  --license Apache-2.0 \
  robot_basics
```

理解：

```text
package.xml
setup.py
setup.cfg
resource/
robot_basics/
```

完成一个最简单节点：

```python
import rclpy
from rclpy.node import Node


class HelloNode(Node):
    def __init__(self) -> None:
        super().__init__("hello_node")
        self.get_logger().info("Hello ROS2")


def main(args=None) -> None:
    rclpy.init(args=args)
    node = HelloNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

---

### Day 4：Publisher 和 Subscriber

创建两个节点：

```text
distance_publisher
        ↓ /distance
distance_subscriber
```

建议使用：

```text
std_msgs/msg/Float32
```

官方 Python 发布订阅教程提供了创建节点、发布消息和订阅消息的完整步骤。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html?utm_source=chatgpt.com "Writing a simple publisher and subscriber (Python)"))

---

### Day 5：训练距离分类模型

生成训练数据：

```text
输入：距离
标签：safe、slow、danger
```

例如：

```python
x_train = torch.rand(1000, 1)

y_train = torch.zeros(1000, dtype=torch.long)
y_train[x_train[:, 0] <= 0.6] = 1
y_train[x_train[:, 0] <= 0.3] = 2
```

需要完成：

-  定义模型
    
-  定义损失
    
-  定义优化器
    
-  训练若干轮
    
-  计算准确率
    

> 这个问题用规则判断更合适。这里使用神经网络只是为了学习完整的 PyTorch 流程。

---

### Day 6：整理

项目结构：

```text
ros2_ws/src/robot_basics/
├── robot_basics/
│   ├── distance_publisher.py
│   └── distance_subscriber.py
├── package.xml
├── setup.py
└── setup.cfg

ml/scripts/
├── train_distance_classifier.py
└── test_distance_classifier.py
```

本周验收：

-  能独立写 Publisher
    
-  能独立写 Subscriber
    
-  能写一个基本训练循环
    
-  能解释 loss 和 optimizer 的作用
    

---

## 第 3 周：图像数据处理与 ROS 2 运动控制

### 本周目标

- 理解图像数据
    
- 使用 OpenCV 读取和处理图片
    
- 使用 Dataset 和 DataLoader
    
- 学会发布 `/cmd_vel`
    
- 完成基础控制节点
    

### 时间分配

|内容|时间|
|---|--:|
|OpenCV 与 PyTorch|9 小时|
|ROS 2 控制|6 小时|
|整理|2 小时|

---

### Day 1：OpenCV 图像基础

学习：

- 图像的高度、宽度和通道
    
- RGB 与 BGR
    
- 图片读取
    
- 图片缩放
    
- 灰度化
    
- 阈值处理
    
- 摄像头或视频读取
    

OpenCV 官方 Python 教程覆盖图像读取、图像处理、视频处理、特征检测和相机标定等内容。([OpenCV 文档](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html "OpenCV: OpenCV-Python Tutorials"))

练习：

```python
import cv2

image = cv2.imread("test.jpg")

if image is None:
    raise FileNotFoundError("无法读取 test.jpg")

resized = cv2.resize(image, (224, 224))
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

cv2.imwrite("gray.jpg", gray)
```

---

### Day 2：Dataset 和 DataLoader

学习：

- `Dataset`
    
- `DataLoader`
    
- batch size
    
- shuffle
    
- train/validation 划分
    

PyTorch 使用 `Dataset` 保存样本与标签，使用 `DataLoader` 按 batch 提供训练数据。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html?utm_source=chatgpt.com "Datasets & DataLoaders"))

---

### Day 3：准备视觉指令数据集

分类类别：

```text
left
right
forward
stop
```

目录：

```text
ml/data/command_dataset/
├── train/
│   ├── left/
│   ├── right/
│   ├── forward/
│   └── stop/
└── val/
    ├── left/
    ├── right/
    ├── forward/
    └── stop/
```

每类最低准备：

```text
训练集：50张
验证集：10～20张
```

推荐目标：

```text
训练集：每类100～200张
验证集：每类20～40张
```

数据应包含：

- 不同角度
    
- 不同距离
    
- 不同亮度
    
- 不同背景
    
- 轻微旋转
    
- 部分遮挡
    

`ImageFolder` 可以根据文件夹名称自动生成类别标签，适合这种按类别建立文件夹的数据集。([PyTorch Docs](https://docs.pytorch.org/vision/stable/generated/torchvision.datasets.ImageFolder.html?utm_source=chatgpt.com "ImageFolder — Torchvision 0.27 documentation"))

---

### Day 4：图像 Transforms

学习：

- Resize
    
- RandomRotation
    
- RandomResizedCrop
    
- ColorJitter
    
- ToDtype
    
- Normalize
    

Torchvision 的 Transforms 可同时用于训练增强和推理预处理。([PyTorch Docs](https://docs.pytorch.org/vision/stable/transforms.html?utm_source=chatgpt.com "Transforming images, videos, boxes and more"))

注意：

```text
训练阶段：可以使用随机增强
验证阶段：不能使用随机增强
推理阶段：必须与验证阶段保持一致
```

---

### Day 5：ROS 2 速度控制

学习：

```text
geometry_msgs/msg/Twist
/cmd_vel
linear.x
angular.z
```

实现：

```text
forward → linear.x > 0
left    → angular.z > 0
right   → angular.z < 0
stop    → 所有速度为0
```

建立：

```text
command_publisher
        ↓ /robot_command
velocity_controller
        ↓ /cmd_vel
```

---

### Day 6：Launch 和参数

学习：

- ROS 2 参数
    
- launch 文件
    
- 一次启动多个节点
    
- 参数化速度和转向角速度
    

ROS 2 launch 文件用于同时启动和配置多个节点。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html?utm_source=chatgpt.com "Launch — ROS 2 Documentation: Jazzy documentation"))

本周验收：

-  数据集目录建立完成
    
-  能使用 ImageFolder 读取数据
    
-  能显示一个 batch 图片
    
-  能发布 Twist 速度消息
    
-  能使用 launch 启动两个节点
    

---

## 第 4 周：CNN 与 TurtleBot 3 仿真

### 本周目标

- 理解 CNN 基本结构
    
- 跑通一个图像分类网络
    
- 启动 TurtleBot 3 Gazebo 仿真
    
- 观察 `/scan`、`/odom` 和 `/cmd_vel`
    

### 时间分配

|内容|时间|
|---|--:|
|PyTorch CNN|8 小时|
|TurtleBot 3 仿真|7 小时|
|整理|2 小时|

---

### Day 1：CNN 基本概念

学习：

- 卷积层
    
- 卷积核
    
- 通道
    
- 特征图
    
- 池化
    
- Flatten
    
- 全连接层
    

不用深挖数学推导，先理解数据尺寸变化：

```text
3 × 224 × 224
→ Conv
→ ReLU
→ Pool
→ 更多特征图
→ Flatten
→ 分类结果
```

---

### Day 2：跑通官方图像分类示例

完成：

- 加载公开数据集
    
- 定义 CNN
    
- 训练
    
- 验证
    
- 输出准确率
    

PyTorch 的 60 Minute Blitz 和基础教程适合建立完整的图像分类流程。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/deep_learning_60min_blitz.html?utm_source=chatgpt.com "Deep Learning with PyTorch: A 60 Minute Blitz"))

---

### Day 3：TurtleBot 3 仿真安装与启动

目标：

```text
启动Gazebo
→ 加载世界
→ 生成TurtleBot3
→ 使用键盘控制
```

TurtleBot 3 官方提供 RViz fake node 和 Gazebo 两类仿真。需要传感器、SLAM 或导航时，应使用支持 IMU、激光雷达和摄像头等传感器的 Gazebo 仿真。([ROBOTIS e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/?utm_source=chatgpt.com "TurtleBot 3 Simulation"))

---

### Day 4：观察机器人 Topic

重点观察：

```bash
ros2 topic list
ros2 topic echo /scan
ros2 topic echo /odom
ros2 topic info /cmd_vel
ros2 topic hz /scan
```

理解：

|Topic|含义|
|---|---|
| `/scan` |激光雷达数据|
| `/odom` |里程计|
| `/tf` |坐标变换|
| `/cmd_vel` |速度指令|

---

### Day 5：URDF、TF 与 RViz 入门

只学习基础概念：

```text
link  = 机器人刚体
joint = 两个刚体之间的连接
TF    = 不同坐标系之间的关系
URDF  = 机器人结构描述
```

在 RViz 中观察：

```text
map
odom
base_link
laser
```

ROS 2 官方 URDF 教程包含从零建立模型、添加关节、碰撞属性、Xacro 和 `robot_state_publisher`。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html?utm_source=chatgpt.com "URDF — ROS 2 Documentation: Jazzy documentation"))

---

### Day 6：周项目

完成：

```text
启动Gazebo
→ 启动TurtleBot3
→ 自己的ROS2节点发布/cmd_vel
→ 小车按命令运动
```

本周验收：

-  Gazebo 正常启动
    
-  TurtleBot 3 可以键盘控制
    
-  能在 RViz 看到机器人和雷达
    
-  能解释 `map → odom → base_link`
    
-  CNN 训练脚本可以正常运行
    

---

## 第 5 周：视觉模型训练与激光雷达避障

### 本周目标

- 训练自己的视觉指令分类器
    
- 保存和加载模型
    
- 编写雷达避障节点
    
- 建立机器人安全控制逻辑
    

### 时间分配

|内容|时间|
|---|--:|
|模型训练|9 小时|
|雷达避障|6 小时|
|分析整理|2 小时|

---

### Day 1：训练自己的 CNN

输入：

```text
left/right/forward/stop图片
```

输出：

```text
4维logits
```

记录：

- 训练 loss
    
- 验证 loss
    
- 训练 accuracy
    
- 验证 accuracy
    

---

### Day 2：迁移学习

小型自定义数据集通常不适合从零训练大型 CNN，因此可以使用预训练模型进行迁移学习。PyTorch 官方迁移学习教程演示了在小型数据集上微调预训练分类模型。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html?utm_source=chatgpt.com "Transfer Learning for Computer Vision Tutorial"))

推荐选择一个轻量模型，例如：

```text
MobileNet
ResNet18
```

只需掌握：

```text
加载预训练权重
→ 替换最后分类层
→ 冻结或部分冻结特征层
→ 训练自己的4分类任务
```

---

### Day 3：模型保存与加载

需要掌握：

```python
torch.save(model.state_dict(), "command_model.pth")
```

加载时：

```python
model.load_state_dict(
    torch.load("command_model.pth", weights_only=True)
)
model.eval()
```

PyTorch 官方推荐保存模型的 `state_dict`，加载推理时重新创建模型结构并调用 `load_state_dict()`。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html?utm_source=chatgpt.com "Saving and Loading Models — PyTorch Tutorials 2.13.0+ ..."))

---

### Day 4：读取 LaserScan

建立节点：

```text
lidar_safety_node
```

输入：

```text
/scan
```

输出：

```text
/obstacle_state
```

逻辑：

```text
取雷达正前方一定角度范围
→ 过滤inf和nan
→ 计算最小距离
→ 判断safe/warning/danger
```

推荐状态：

```text
距离 > 0.6m       → safe
0.35m～0.6m      → warning
距离 < 0.35m     → danger
```

---

### Day 5：完成基础避障

控制逻辑：

```text
safe    → 前进
warning → 减速
danger  → 停止并转弯
```

暂时不使用神经网络做避障。

雷达安全控制属于明确规则问题，使用规则通常更容易解释、调试和保证安全。

---

### Day 6：模型评估

检查：

- 哪一类最容易识别错误
    
- 背景变化是否影响模型
    
- 光照变化是否影响模型
    
- 左右箭头是否容易混淆
    
- 模型置信度是否合理
    

本周验收：

-  自定义视觉模型训练完成
    
-  模型文件保存成功
    
-  单张图片推理成功
    
-  Gazebo 小车能够基础避障
    
-  完成训练曲线图
    

---

## 第 6 周：PyTorch 模型接入 ROS 2

### 本周目标

- 将训练和推理解耦
    
- 编写模型推理节点
    
- 发布视觉识别结果
    
- 建立统一决策节点
    

### 时间分配

|内容|时间|
|---|--:|
|推理代码重构|6 小时|
|ROS 2 模型节点|7 小时|
|系统整合|4 小时|

---

### Day 1：重构推理代码

将机器学习代码拆分为：

```text
ml/
├── train.py
├── evaluate.py
├── infer.py
├── model.py
├── dataset.py
└── config.py
```

`infer.py` 应提供一个清晰接口：

```python
command, confidence = classifier.predict(image)
```

输出示例：

```text
command = "left"
confidence = 0.91
```

---

### Day 2：文件图片推理节点

第一版不接摄像头。

节点：

```text
vision_inference_node
```

流程：

```text
读取测试图片
→ OpenCV预处理
→ 转换为Tensor
→ PyTorch推理
→ 发布结果
```

输出 Topic：

```text
/vision_command
```

第一版消息可使用：

```text
std_msgs/msg/String
```

---

### Day 3：加入置信度

建议再发布：

```text
/vision_confidence
```

或者定义自定义消息：

```text
string command
float32 confidence
```

决策规则：

```text
confidence ≥ 0.75 → 接受识别结果
confidence < 0.75 → 发布unknown
```

---

### Day 4：决策节点

建立：

```text
decision_node
```

订阅：

```text
/vision_command
/vision_confidence
/obstacle_state
```

发布：

```text
/cmd_vel
```

优先级：

```text
1. obstacle_state == danger
   → 立即停止或转弯

2. vision_confidence过低
   → 停止

3. 雷达安全且识别可信
   → 执行视觉命令
```

---

### Day 5：接入图片 Topic

进阶版本：

```text
/camera/image_raw
        ↓
vision_inference_node
        ↓
/vision_command
```

初期可以使用：

- 摄像头
    
- 视频文件
    
- 定时发布的图片
    
- Gazebo 虚拟相机
    

不建议第一天同时调试 Gazebo 相机、ROS 消息转换和 PyTorch 模型。先确保文件推理版本正确，再替换输入来源。

---

### Day 6：Launch 整合

建立：

```text
robot_bringup/
└── launch/
    └── vision_robot.launch.py
```

一次启动：

```text
lidar_safety_node
vision_inference_node
decision_node
```

本周验收：

-  PyTorch 模型能在 ROS 2 节点中加载
    
-  节点能发布分类结果
    
-  雷达危险时能覆盖视觉命令
    
-  多个节点可以通过 launch 启动
    

---

## 第 7 周：SLAM、Nav 2 与系统完善

### 本周目标

- 体验 SLAM 建图
    
- 了解 Nav 2 导航框架
    
- 将视觉项目与导航概念区分开
    
- 提高系统稳定性
    

### 时间分配

|内容|时间|
|---|--:|
|SLAM|5 小时|
|Nav 2|6 小时|
|项目优化|6 小时|

---

### Day 1～2：SLAM 建图

流程：

```text
启动Gazebo世界
→ 启动SLAM
→ 遥控机器人探索
→ RViz生成地图
→ 保存地图
```

TurtleBot 3 官方提供了 Gazebo 中的 SLAM 仿真流程。([ROBOTIS e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/slam_simulation/?utm_source=chatgpt.com "TurtleBot 3 SLAM simulation manual"))

完成：

```text
maps/
├── summer_map.pgm
└── summer_map.yaml
```

---

### Day 3～4：Nav 2 入门

学习：

- 地图
    
- 定位
    
- 全局规划
    
- 局部规划
    
- Costmap
    
- 行为树
    
- Action
    
- 恢复行为
    

Nav 2 Getting Started 会带领用户安装 Nav 2，并让模拟 TurtleBot 3 在 Gazebo 中完成导航。([Nav 2](https://docs.nav2.org/getting_started/index.html?utm_source=chatgpt.com "Getting Started — Nav 2 1.0.0 documentation"))

Nav 2 官方建议在学习导航前先掌握 ROS 2 基础。([Nav 2](https://docs.nav2.org/concepts/index.html?utm_source=chatgpt.com "Navigation Concepts — Nav 2 1.0.0 documentation"))

完成：

```text
启动地图
→ 设置机器人初始位置
→ 在RViz设置目标点
→ 机器人自动规划并移动
```

---

### Day 5：异常情况处理

为自己的决策节点增加：

- 无雷达数据时停止
    
- 无图像时停止
    
- 模型加载失败时退出并记录日志
    
- 置信度不足时停止
    
- Topic 长时间没有更新时停止
    
- 限制最大线速度和角速度
    

推荐原则：

```text
遇到未知状态时，默认停止，而不是继续运动。
```

---

### Day 6：系统测试

建立测试表：

|测试场景|预期行为|实际行为|是否通过|
|---|---|---|---|
|识别 forward 且前方安全|前进|||
|识别 left 且前方安全|左转|||
|识别 stop|停止|||
|识别 forward 但前方危险|停止或避障|||
|模型置信度低|停止|||
|雷达数据中断|停止|||

本周验收：

-  完成一次 SLAM 建图
    
-  完成一次 Nav 2 目标点导航
    
-  系统具备基本故障保护
    
-  至少完成 5 个场景测试
    

---

## 第 8 周：最终整合、展示与复盘

### 本周目标

- 完成最终项目
    
- 修复明显 Bug
    
- 整理 GitHub
    
- 录制演示视频
    
- 总结下一阶段方向
    

### 时间分配

|内容|时间|
|---|--:|
|整合测试|8 小时|
|文档与展示|6 小时|
|复盘与扩展|3 小时|

---

### Day 1：整理项目结构

推荐结构：

```text
ros2-pytorch-robot/
├── ml/
│   ├── data/
│   ├── models/
│   │   └── command_model.pth
│   ├── scripts/
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   └── infer.py
│   └── notebooks/
├── ros2_ws/
│   └── src/
│       ├── vision_inference/
│       ├── lidar_safety/
│       ├── robot_decision/
│       └── robot_bringup/
├── maps/
├── docs/
│   ├── architecture.md
│   ├── training.md
│   └── troubleshooting.md
├── README.md
├── requirements.txt
└── .gitignore
```

---

### Day 2：完善系统架构

最终节点关系：

```text
/camera/image_raw
        ↓
vision_inference_node
        ↓
/vision_command
/vision_confidence
        ↓
                    ┌─────────────────┐
/scan               │                 │
  ↓                 │  decision_node  │
lidar_safety_node → │                 │
  ↓                 └────────┬────────┘
/obstacle_state              ↓
                          /cmd_vel
                              ↓
                           Gazebo
```

---

### Day 3：性能检查

记录：

- 模型单次推理时间
    
- 图像处理时间
    
- 推理频率
    
- 雷达数据频率
    
- 控制频率
    
- CPU 和内存占用
    

不必追求极致性能。

目标是确保：

```text
推理不会阻塞ROS2节点
速度指令能持续更新
雷达危险信号能及时覆盖视觉命令
```

---

### Day 4：README

README 至少包括：

```markdown
# ROS2 PyTorch Vision Robot

## 项目简介

## 功能演示

## 系统架构

## 开发环境

## 安装方法

## 运行方法

## ROS2节点说明

## Topic说明

## PyTorch模型说明

## 数据集结构

## 训练方法

## 项目效果

## 已知问题

## 后续计划
```

---

### Day 5：录制展示视频

建议演示顺序：

```text
1. 展示Gazebo环境
2. 展示RViz雷达数据
3. 展示模型识别结果
4. 机器人执行left/right/forward/stop
5. 在障碍物前展示安全停止
6. 可选：展示Nav2导航
```

视频长度：

```text
2～4分钟
```

---

### Day 6：暑假复盘

回答以下问题：

```text
1. 我能否独立创建ROS2节点？
2. 我能否读懂一个ROS2项目的节点关系？
3. 我是否理解PyTorch训练和推理的区别？
4. 我能否更换一个新的图像分类数据集？
5. 我能否把新的模型接入ROS2？
6. 我更喜欢感知、控制、导航还是学习算法？
```

---

# 6. 资源索引

## 6.1 PyTorch 主线

### 必学

1. **PyTorch Learn the Basics**
    

学习顺序：

```text
Tensors
→ Datasets & DataLoaders
→ Transforms
→ Build Model
→ Autograd
→ Optimization
→ Save & Load
```

这是整个 PyTorch 部分的主线。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/basics/intro.html?utm_source=chatgpt.com "Learn the Basics — PyTorch Tutorials 2.13.0+cu 130 ..."))

2. **Datasets & DataLoaders**
    

重点学习如何组织数据集和生成 batch。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html?utm_source=chatgpt.com "Datasets & DataLoaders"))

3. **Training with PyTorch**
    

重点学习完整训练循环、损失函数和优化器。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/introyt/trainingyt.html?utm_source=chatgpt.com "Training with PyTorch"))

4. **Saving and Loading Models**
    

用于第 5～6 周模型部署。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html?utm_source=chatgpt.com "Saving and Loading Models — PyTorch Tutorials 2.13.0+ ..."))

### 进阶

5. **Transfer Learning for Computer Vision**
    

用于自定义小型图像数据集。([PyTorch Docs](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html?utm_source=chatgpt.com "Transfer Learning for Computer Vision Tutorial"))

6. **Torchvision ImageFolder**
    

用于根据目录自动加载分类数据集。([PyTorch Docs](https://docs.pytorch.org/vision/stable/generated/torchvision.datasets.ImageFolder.html?utm_source=chatgpt.com "ImageFolder — Torchvision 0.27 documentation"))

7. **Torchvision Transforms**
    

用于数据增强和图像预处理。([PyTorch Docs](https://docs.pytorch.org/vision/stable/transforms.html?utm_source=chatgpt.com "Transforming images, videos, boxes and more"))

---

## 6.2 ROS 2 主线

1. **ROS 2 Jazzy Tutorials**
    

作为 ROS 2 学习总入口。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials.html?utm_source=chatgpt.com "Tutorials — ROS 2 Documentation: Jazzy documentation"))

2. **Beginner CLI Tools**
    

学习 node、topic、service、parameter、action、launch 和 rosbag。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Beginner-CLI-Tools.html?utm_source=chatgpt.com "Beginner: CLI tools - Jazzy documentation"))

3. **Python Publisher and Subscriber**
    

用于第 2 周。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html?utm_source=chatgpt.com "Writing a simple publisher and subscriber (Python)"))

4. **Python Service and Client**
    

作为选学内容，不是项目核心。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Service-And-Client.html?utm_source=chatgpt.com "Writing a simple service and client (Python)"))

5. **Launch Tutorials**
    

用于统一启动系统。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Launch/Launch-Main.html?utm_source=chatgpt.com "Launch — ROS 2 Documentation: Jazzy documentation"))

6. **URDF Tutorials**
    

用于理解机器人模型和坐标结构。([ROS Docs](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html?utm_source=chatgpt.com "URDF — ROS 2 Documentation: Jazzy documentation"))

---

## 6.3 Gazebo 与 TurtleBot 3

1. **Gazebo Harmonic Getting Started**
    

学习 Gazebo 安装、运行、世界和机器人基础。([Gazebo](https://gazebosim.org/docs/harmonic/getstarted/ "Getting Started with Gazebo? — Gazebo harmonic documentation"))

2. **Gazebo 与 ROS 版本搭配**
    

ROS 2 Jazzy 推荐搭配 Gazebo Harmonic。([Gazebo](https://gazebosim.org/docs/harmonic/ros_installation/ "Installing Gazebo with ROS — Gazebo harmonic documentation"))

3. **TurtleBot 3 Simulation**
    

用于启动仿真机器人。([ROBOTIS e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/?utm_source=chatgpt.com "TurtleBot 3 Simulation"))

4. **TurtleBot 3 SLAM Simulation**
    

用于第 7 周建图。([ROBOTIS e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/slam_simulation/?utm_source=chatgpt.com "TurtleBot 3 SLAM simulation manual"))

5. **TurtleBot 3 Navigation Simulation**
    

用于 Nav 2 导航练习。([ROBOTIS e-Manual](https://emanual.robotis.com/docs/en/platform/turtlebot3/nav_simulation/?utm_source=chatgpt.com "Navigation Simulation"))

---

## 6.4 Nav 2

1. **Nav 2 Getting Started**
    

带领用户在 Gazebo 中运行模拟 TurtleBot 3 导航。([Nav 2](https://docs.nav2.org/getting_started/index.html?utm_source=chatgpt.com "Getting Started — Nav 2 1.0.0 documentation"))

2. **Nav 2 Navigation Concepts**
    

学习定位、规划、Costmap 和导航框架。([Nav 2](https://docs.nav2.org/concepts/index.html?utm_source=chatgpt.com "Navigation Concepts — Nav 2 1.0.0 documentation"))

3. **Navigating While Mapping**
    

完成基础 Nav 2 后再选学。([Nav 2](https://docs.nav2.org/tutorials/docs/navigation2_with_slam.html?utm_source=chatgpt.com "Navigating while Mapping (SLAM)"))

---

## 6.5 OpenCV

使用 OpenCV 官方 Python 教程，重点学习：

```text
图片读取
图片缩放
颜色空间
视频读取
阈值处理
轮廓和简单特征
```

([OpenCV 文档](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html "OpenCV: OpenCV-Python Tutorials"))

---

# 7. 每周 Git 提交规范

建议每天使用：

```bash
git status
git add .
git commit -m "feat: complete tensor distance classification"
git push
```

提交信息示例：

```text
feat: add ROS2 distance publisher
feat: implement lidar safety node
feat: train command image classifier
feat: integrate PyTorch inference with ROS2
fix: handle invalid lidar ranges
docs: add project architecture
```

避免：

```text
update
change
test
123
```

---

# 8. 项目分级目标

## 最低目标：MVP

暑假时间不够时，优先完成：

-  ROS 2 Publisher 和 Subscriber
    
-  Gazebo 小车控制
    
-  激光雷达避障
    
-  PyTorch 四分类模型
    
-  模型结果通过 ROS 2 发布
    
-  雷达优先的决策节点
    

完成这些就算项目成功。

## 标准目标

在 MVP 基础上增加：

-  ROS 图像 Topic
    
-  置信度判断
    
-  launch 统一启动
    
-  数据集增强
    
-  完整 README
    
-  演示视频
    

## 挑战目标

标准目标完成后再增加：

-  SLAM 建图
    
-  Nav 2 目标点导航
    
-  自定义 ROS 2 消息
    
-  ONNX 模型导出
    
-  推理性能测试
    
-  C++重写控制节点
    

不要在 MVP 完成前做挑战目标。

---

# 9. 暂时不学的内容

暑假第一阶段暂时跳过：

- Transformer 底层实现
    
- 大语言模型训练
    
- CUDA 编程
    
- 分布式训练
    
- 强化学习
    
- Diffusion Policy
    
- VLA 微调
    
- Isaac Lab 大规模并行训练
    
- 复杂机械臂控制
    
- ROS 2 DDS 底层实现
    
- 高级 C++模板编程
    

这些内容后续都可能有用，但现在会分散项目主线。

---

# 10. 最终验收清单

## PyTorch

-  熟悉 Tensor 和 shape
    
-  会使用 Dataset 和 DataLoader
    
-  会定义 `nn.Module`
    
-  会写训练和验证循环
    
-  会计算 loss 和 accuracy
    
-  会保存和加载模型
    
-  会进行单张图片推理
    
-  会使用预训练模型做迁移学习
    

## ROS 2

-  会创建 Python Package
    
-  会编写 Node
    
-  会发布和订阅 Topic
    
-  会读取 LaserScan
    
-  会发布 Twist
    
-  会使用 Parameter
    
-  会编写 Launch
    
-  会使用 RViz
    
-  能基本理解 TF 和 URDF
    

## 仿真与导航

-  会启动 Gazebo
    
-  会启动 TurtleBot 3
    
-  会控制机器人移动
    
-  会查看雷达和里程计数据
    
-  会完成基础避障
    
-  可选：会进行 SLAM 建图
    
-  可选：会使用 Nav 2 设置目标点
    

## 项目工程

-  项目上传 GitHub
    
-  目录结构清晰
    
-  README 完整
    
-  依赖可以复现
    
-  有系统架构图
    
-  有训练曲线
    
-  有测试记录
    
-  有演示视频
    

---

# 11. 第一周立即执行清单

今天直接完成以下任务：

```text
1. 创建ros2-pytorch-robot仓库
2. 建立ml、ros2_ws和docs目录
3. 创建Python虚拟环境
4. 验证import torch
5. 验证ros2命令
6. 完成tensor_basics.py
7. 运行turtlesim并观察节点和Topic
8. 提交第一次Git commit
```

第一周不要追求“理解深度学习全部数学”，也不要急着进入 Gazebo。先保证：

```text
PyTorch代码能够运行
ROS2环境能够运行
GitHub能够正常同步
每一天都有小成果
```