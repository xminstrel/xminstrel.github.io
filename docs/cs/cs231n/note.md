semantic gap
为什么研究机器视觉的时候都是在研究猫呢


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

