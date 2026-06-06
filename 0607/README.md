https://kns.cnki.net/kcms2/article/abstract?v=coorgAOmZmCgah0eHIK_XhmAOgKJyuhNT4IqFz-7jDMFh04h4etV_NAGCczWlziuyUJPukKsmQkYVFg5PbIdyo4kAviJfDr8YkIskVRTm3ZON5UHzjNz9V7ZBNVdfQs3xYD3hmbAoFjqfvuFCj5nDVDkyV18SzPDGjmnBW6r9-Q=&uniplatform=NZKPT
结合网络资料


研究方向
系统梳理YOLO系列算法演进，研究了常用的损失函数、数据集、指标和性能评估。


网络结构
分为主干Backbone、颈部Neck、头部Head

YOLOv1
主干：类GoogleNet，24个卷积层和2个全连接层，输入 448x448
颈部：无
头部：全连接层，2个预测边界框，输出 7×7

YOLOv2
主干：Darknet-19，19个卷积层和5个最大池化，输入 416x416
颈部：Passthrough拆分重组浅层特征
头部：移除全连接层，引入锚框，通过计算中心偏移量和宽高缩放比来预测边界框，输出 13x13

YOLOv3
主干：Darknet-53，输出为输入的 1/32，移除池化层和全连接层，改变卷积核步长
颈部：特征金字塔网络(Feature PyramidNetwork, FPN)，使用52x52、26x26、13x13共3种尺度，用于检测小、中、大目标
头部：每种尺度预测3个锚框

YOLOv4
主干：CSPDarknet-53，删去了最后的池化层、全连接层以及Softmax层
颈部：引入空间金字塔池化(Spatial Pyramid Pooling, SPP)扩大感受野，路径聚合网络(Path Aggregation Network, PANet)自底向上传递特征
头部：基本沿用v3

YOLOv5
基本结构与YOLOv4类似，根据不同通道的尺度缩放

YOLOX
依据YOLOv3和YOLOv5，使用了CSPNet，SiLU激活函数以及PANet


轻量化
1 通过深度可分离卷积、分组卷积、可调超参数降低空间分辨率和减少通道数
2 压缩整体网络参数，减少卷积层，精简模型体积

注意力
空间型：注重目标位置
通道型：注重目标特征
混合型


损失函数
损失函数 = 模型的边界框损失 + 模型的目标置信度损失 + 模型的预测目标类别损失

YOLOv1-v2：MSE均方误差
YOLOv3：二分类交叉熵，引入权重对不包含目标物体的置信度进行约束
YOLOv4：CIoU(Complete-IoU)，考虑重叠面积、中心点距离和长宽比


激活函数
YOLOv1-v2：Softmax
YOLOv3：Logistic
YOLOv4：Mish
YOLOv5：中间层LeakyReLU，检测层Sigmoid
YOLOR、YOLOX：SiLU


数据集

VOC
构成：train/val/test或trainval/test
物体可分4大类，20小类，不同类实例数量和检测难度不同
评价指标：IoU = 0.5

COCO
构成：train/val/test
多目标，部分对象存在遮挡与噪声，包含各种尺寸的物体，超过300000张图片，超过2000000个实例，80个目标类别
评价指标：IoU = arange(0.5, 1.0, 0.05)，分别计算大、中、小3类物体

VisDrone
构成：train/val/test
包括图像和视频，数据集场景复杂，遮挡情况严重，同时标签密集
评价指标：同COCO

YOLOv4之后的模型一般使用COCO数据集


训练方式
YOLOv1：MSE优化
YOLOv2：引入多尺度训练，每隔若干个batch随机切换输入图像尺寸
YOLOv3：多尺度预测（52x52、26x26、13x13）
YOLOv4：引入Mosaic数据增强，裁剪拼接训练图像
YOLOv5：引入自适应学习率调整