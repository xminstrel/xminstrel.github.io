# Win 11 上用 WSL 安装 Ubuntu 24.04 + ROS 2 Jazzy

这套方案适合你现在这种情况：  
**Windows 11 主系统不动，在 WSL 里装 Ubuntu 24.04，然后在里面装 ROS 2 Jazzy。**  
ROS 2 官方推荐用 Ubuntu 24.04 的 deb 包来安装 Jazzy；WSL 也支持直接运行 Linux 图形界面程序。([ROS Docs](https://docs.ros.org/en/jazzy/Installation.html "Installation — ROS 2 Documentation: Jazzy  documentation"))

---

## 一、先确认 WSL 现在是什么状态

先在 **PowerShell（建议管理员打开）** 里运行：

```powershell
wsl --status
wsl -l -v
```

`wsl -l -v` 可以查看你已经安装了哪些 Linux 发行版，以及它们是不是 **WSL 2**。微软文档说明，用 `wsl --install` 安装的新 Linux 发行版默认会是 **WSL 2**。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/install "Install WSL | Microsoft Learn"))

如果你还没看到 Ubuntu，就继续下面安装。

---

## 二、安装 Ubuntu 24.04

先看看可安装的发行版列表：

```powershell
wsl --list --online
```

微软官方说明，可以用这个命令查看可在线安装的发行版，再用 `wsl --install -d <DistroName>` 指定安装。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/install "Install WSL | Microsoft Learn"))

然后直接安装 Ubuntu 24.04：

```powershell
wsl --install Ubuntu-24.04
```

Ubuntu 官方 WSL 文档也给了这个安装写法，并说明 Ubuntu 24.04 现在采用新的 WSL 发行版格式。这个新格式要求 **WSL 2.4.10 或更高版本**。([Ubuntu 文档](https://documentation.ubuntu.com/wsl/latest/howto/install-ubuntu-wsl2/ "Install Ubuntu on WSL 2 - Ubuntu on WSL documentation"))

如果这个命令不行，你也可以试微软文档里的指定安装格式：

```powershell
wsl --install -d Ubuntu-24.04
```

如果安装过程卡住，微软建议改用：

```powershell
wsl --install --web-download -d Ubuntu-24.04
```

这是官方给出的备用方式。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/install "Install WSL | Microsoft Learn"))

---

## 三、第一次进入 Ubuntu

安装完成后，直接运行：

```powershell
wsl -d Ubuntu-24.04
```

或者如果它已经是默认发行版，也可以直接：

```powershell
wsl
```

微软文档说明，安装完成并重启后，系统会继续初始化，并要求你创建一个 **Linux 用户名和密码**。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps "Run Linux GUI apps with WSL | Microsoft Learn"))

这里注意：

- 这个用户名密码是 **Ubuntu 里的**
    
- 和你的 Windows 密码不是一回事
    
- 输入密码时终端里不会显示字符，这是正常现象
    

---

## 四、更新 WSL 和 Ubuntu

先在 **PowerShell** 里更新 WSL：

```powershell
wsl --update
wsl --shutdown
```

WSL 的 GUI 支持文档建议先更新 WSL，再重启 WSL 环境让更新生效。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps "Run Linux GUI apps with WSL | Microsoft Learn"))

然后重新进入 Ubuntu：

```powershell
wsl -d Ubuntu-24.04
```

在 Ubuntu 里更新系统：

```bash
sudo apt update
sudo apt upgrade -y
```

---

## 五、确认你现在就在 Ubuntu 24.04 里

运行：

```bash
cat /etc/os-release
uname -a
```

如果看到类似：

- `Ubuntu 24.04`
    
- `Noble`
    

那就对了。

---

## 六、安装 ROS 2 Jazzy

ROS 2 官方写得很明确：  
**Jazzy 的 Ubuntu deb 包对应 Ubuntu Noble 24.04。** 官方也把 deb 安装作为推荐方式。([ROS Docs](https://docs.ros.org/en/jazzy/Installation.html "Installation — ROS 2 Documentation: Jazzy  documentation"))

### 1）设置 UTF-8 locale

```bash
locale
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale
```

这是 ROS 2 Jazzy 官方安装页给出的系统准备步骤。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

### 2）启用 Universe 仓库并配置 ROS 源

```bash
sudo apt install software-properties-common -y
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

这些命令也是 Jazzy 官方安装文档给出的标准配置方式。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

### 3）安装开发工具

```bash
sudo apt update
sudo apt install ros-dev-tools -y
```

官方写明，如果你要开发 ROS 包，建议装 `ros-dev-tools`。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

### 4）安装 ROS 2 Jazzy 桌面版

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install ros-jazzy-desktop -y
```

`ros-jazzy-desktop` 是官方推荐的桌面安装，包含 ROS、RViz、demos、tutorials。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

如果你只想装最基础的命令行版本，可以换成：

```bash
sudo apt install ros-jazzy-ros-base -y
```

但你要学可视化和教程，建议直接装 `desktop`。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

---

## 七、配置环境变量

每次打开终端都要先 source 一次：

```bash
source /opt/ros/jazzy/setup.bash
```

ROS 2 Jazzy 官方文档就是这样写的。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

为了以后方便，直接写进 `~/.bashrc`：

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

---

## 八、验证 ROS 2 是否安装成功

官方推荐用 talker / listener 示例来验证。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

### 终端 1

```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_cpp talker
```

### 终端 2

```bash
source /opt/ros/jazzy/setup.bash
ros2 run demo_nodes_py listener
```

如果你看到：

- talker 在持续 `Publishing`
    
- listener 在持续 `I heard`
    

说明 ROS 2 的 C++ 和 Python 运行都正常。([ROS Docs](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html "Ubuntu (deb packages) — ROS 2 Documentation: Jazzy  documentation"))

---

## 九、验证 GUI 是否正常

微软官方说明，WSL 现在支持 Linux GUI 应用，能以集成方式在 Windows 上显示，支持 X 11 和 Wayland；Linux 程序会像普通 Windows 程序一样弹窗。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps "Run Linux GUI apps with WSL | Microsoft Learn"))

### 方法 1：直接试 RViz 2

如果你已经装了 `ros-jazzy-desktop`，可以直接运行：

```bash
source /opt/ros/jazzy/setup.bash
rviz2
```

如果弹出 RViz 2 窗口，就说明 GUI 基本正常。

### 方法 2：先用简单 GUI 程序测试

如果你想先测试最基础的图形界面，可以装一个简单编辑器：

```bash
sudo apt install gedit -y
gedit
```

如果 `gedit` 能弹出窗口，说明 WSLg 基本正常。微软文档确认 WSL GUI 应用是官方支持的集成体验。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps "Run Linux GUI apps with WSL | Microsoft Learn"))

---

## 十、常见问题

### 1）`wsl --install` 之后输入 `wsl` 进不去

先看状态：

```powershell
wsl --status
wsl -l -v
```

如果没有 Ubuntu，就重新装：

```powershell
wsl --install -d Ubuntu-24.04
```

微软官方明确说，如果 `wsl --install` 只显示帮助文本，可以先 `wsl --list --online`，再 `wsl --install -d <DistroName>`。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/install "Install WSL | Microsoft Learn"))

### 2）GUI 程序打不开

先更新：

```powershell
wsl --update
wsl --shutdown
```

再确认你是 Windows 11，或者满足微软文档所列的 GUI 支持前提。微软文档写明，Linux GUI 应用需要 Windows 10 Build 19044+ 或 Windows 11。([微软学习](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps "Run Linux GUI apps with WSL | Microsoft Learn"))

### 3）`Ubuntu-24.04` 安装失败

可以改用 Ubuntu 官方提供的 `.wsl` 镜像：

1. 去 Ubuntu 24.04 的发布页下载 `.wsl`
    
2. 双击安装，或者在下载目录执行：
    

```powershell
wsl --install --from-file <image>.wsl
```

这是 Ubuntu 官方 WSL 文档给出的安装方式。([Ubuntu 文档](https://documentation.ubuntu.com/wsl/latest/howto/install-ubuntu-wsl2/ "Install Ubuntu on WSL 2 - Ubuntu on WSL documentation"))

---

## 十一、你现在最推荐的实际做法

你可以直接按这份最短流程跑：

### PowerShell

```powershell
wsl --status
wsl -l -v
wsl --list --online
wsl --install -d Ubuntu-24.04
wsl --update
wsl --shutdown
wsl -d Ubuntu-24.04
```

### Ubuntu

```bash
sudo apt update
sudo apt upgrade -y

sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt install software-properties-common -y
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y

export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb

sudo apt update
sudo apt upgrade -y
sudo apt install ros-dev-tools -y
sudo apt install ros-jazzy-desktop -y

echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 测试

```bash
ros2 run demo_nodes_cpp talker
```

新开一个 Ubuntu 终端：

```bash
ros2 run demo_nodes_py listener
```

GUI 测试：

```bash
rviz2
```

你把你当前执行到哪一步、报错截图或终端输出发我，我可以继续按这份教程陪你一步一步排。