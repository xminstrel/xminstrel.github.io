semantic gap
为什么研究机器视觉的时候都是在研究猫呢

## assignment 1

## 2.图像分类与线性分类器

机器学习的流程：
1. 收集数据集和标签
2. 用机器学习算法训练分类器
3. 在新图像上评价分类器


### Nearest Neighbor KNN
距离函数，判断目标图像和标记图像的相似度，输出标签
![](assets/note.png)
![](assets/note-1.png)


曼哈顿距离 L1 对特征值敏感，比如旋转则特征值将改变

超参数问题 hyperparameters

![](assets/note-2.png)

测试集、训练集、验证集

![](assets/note-3.png)

交叉验证


CIFAR10 数据集



### Linear Classifier
线性分类器
$$
f(x,W,b)=Wx+b
$$
权重，偏置
![](assets/note-5.png)

![](assets/note-4.png)

从代数视角看一个 2×2 像素图像，变成向量，输入线性函数，映射得到分数进行分类

 ![](assets/note-6.png)

线性分类器权重：
![](assets/note-7.png)


损失函数 衡量预测分数与真实分数之间的差异

![](assets/note-8.png)

### Softmax Classifier

![](assets/note-9.png)

思路：
1. 把 score 转成“概率形式”
2. 用正确类别的概率计算 loss

linear classifier + softmax + loss

softmax 公式：全部分数取指数然后归一化


概率由 softmax 定义
正确类别概率取负值再取对数得到损失函数

KL 函数
交叉熵函数
BCE 二元交叉熵

## 3. Regularization and Optimization
正则化与优化

正则化目的，让训练集预测差一点但是测试集表现好一点，也就是防止过拟合

![](assets/note-10.png)

![](assets/note-11.png)


optimize
损失景观
 Gradient Descent梯度下降
![](assets/note-13.png)
![](assets/note-12.png)

随机梯度下降
![](assets/note-14.png)

优化 SGD+动量
![](assets/note-15.png)

优化 RMSProp

![](assets/note-16.png)
![](assets/note-17.png)

优化 Adam

![](assets/note-18.png)

![](assets/note-19.png)


学习率
调度器
线形缩放定律

![](assets/note-20.png)

## 神经网络与反向传播
激活函数 Activation functions
ReLU 激活函数引入非线性变换
sigmoid

![](assets/note-21.png)

![](assets/note-22.png)



调整正则化超参数


计算图
![](assets/note-23.png)

![](assets/note-24.png) 


反向传播
人怎么能这么聪明
![](assets/note-25.png)


![](assets/note-26.png)

![](assets/note-27.png)


![](assets/note-28.png)

![](assets/note-29.png)


# 感知和理解视觉世界

## 卷积神经网络
算子：卷积层、池化层


特征提取范式，淘汰了


卷积网络，端到端学习方式

卷积层、全连接层

加多个滤波器
![](assets/note-30.png)

滤波器怎么来？梯度下降学习出来的

超参数：训练之前就确定好的参数，比如滤波器大小

![](assets/note-31.png)

卷积层之间加激活函数，非线性提高能力
![](assets/note-32.png)



带不长的卷积，快速增大后面的感受野
![](assets/note-33.png)

最大池化
![](assets/note-34.png)



## CNN 架构

![](assets/note-35.png)

多层网络性能优化，让其不比浅层模型差
residual connection 残差连接
![](assets/note-36.png)

怎么确定初始权重
Weight Initialization

何恺明？
MSRA Initialization

**训练数据不足时如何训练 cnn**

其实是预训练微调

![](assets/note-37.png)
![](assets/note-38.png)

超参数选择


![](assets/note-39.png)
超参数搜索
![](assets/note-40.png)

## 循环神经网络 RNN

工具：weights and biases

![](assets/note-41.png)

构建神经网络 

```

```

![](assets/note-42.png)


## 注意力与 Transformer

Attention and Transformer

Attention layer


编码器以及解码器

![](assets/note-43.png)

## 目标检测、图像分割与可视化


vision transformer（ViT）
patch➡️token➡️add position ➡️
![](assets/note-44.png)

![](assets/note-45.png)

![](assets/note-46.png)