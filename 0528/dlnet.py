import torch
import os
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import transforms, datasets
from torch.utils.data import DataLoader
from torchinfo import summary

class MixedNet(nn.Module):
    def __init__(self):
        super(MixedNet, self).__init__()

        #定义LeakyReLU激活函数，负半轴斜率0.1
        self.leaky_relu = nn.LeakyReLU(negative_slope=0.1)

        #1 卷积层 输入3通道(RGB)，输出16通道，卷积核3×3，padding=1补边1保证特征图尺寸不变
        self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
        #2 池化层 最大池化，池化核2×2，步长2，特征图宽高各缩小为原来1/2
        self.pool1 = nn.MaxPool2d(2, 2)
        
        #3 卷积层 输入16通道，输出32通道，卷积核3×3，padding=1补边1保证特征图尺寸不变
        self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
        #4 池化层 最大池化，池化核2×2，步长2，特征图宽高各缩小为原来1/2
        self.pool2 = nn.MaxPool2d(2, 2)
        
        #5 卷积层 输入32通道，输出64通道，卷积核3×3，padding=1补边1保证特征图尺寸不变
        self.conv3 = nn.Conv2d(32, 64, 3, padding=1)
        #6 池化层 最大池化，池化核2×2，步长2，特征图宽高各缩小为原来1/2
        self.pool3 = nn.MaxPool2d(2, 2)

        #7 卷积层 输入64通道，输出128通道，卷积核3×3，padding=1补边1保证特征图尺寸不变
        self.conv4 = nn.Conv2d(64, 128, 3, padding=1)

        #8 全连接 输入特征总数128*8*8，输出256维特征
        self.fc1 = nn.Linear(128 * 8 * 8, 256)
        #9 全连接 输入256维，输出64维
        self.fc2 = nn.Linear(256, 64)
        #10 全连接 输入64维，输出3维（对应3分类任务）
        self.fc3 = nn.Linear(64, 3)

    def forward(self, x):
        #数据经过卷积1 LeakyReLU激活 池化1
        x = self.leaky_relu(self.conv1(x))
        x = self.pool1(x)

        #数据经过卷积2 LeakyReLU激活 池化2
        x = self.leaky_relu(self.conv2(x))
        x = self.pool2(x)

        #数据经过卷积3 LeakyReLU激活 池化3
        x = self.leaky_relu(self.conv3(x))
        x = self.pool3(x)

        #数据经过卷积4 LeakyReLU激活
        x = self.leaky_relu(self.conv4(x))

        #将多维特征图展平为一维向量，dim=1保留batch维度
        x = torch.flatten(x, 1)

        #第一层全连接 LeakyReLU激活
        x = self.leaky_relu(self.fc1(x))
        #第二层全连接 LeakyReLU激活
        x = self.leaky_relu(self.fc2(x))
        #输出层全连接
        x = self.fc3(x)
        
        return x


#定义测试/验证函数
#model: 网络模型  test_loader: 测试数据加载器  device: 运行设备(cpu/cuda)
def test_model(model, test_loader, device):
    #切换模型为评估模式
    model.eval()
    #记录预测正确的样本总数
    correct = 0
    #记录参与测试的样本总数
    total = 0
    #禁用梯度计算，测试不需要反向传播
    with torch.no_grad():
        #遍历测试集每一个批次数据
        for data, label in test_loader:
            #将图像数据、标签数据迁移到指定设备
            data, label = data.to(device), label.to(device)
            #模型前向传播，得到预测结果
            out = model(data)
            #取预测概率最大值对应的索引，作为预测类别
            _, pred = torch.max(out, dim=1)
            #累加当前批次样本数量
            total += label.size(0)
            #统计当前批次预测正确的数量并累加
            correct += (pred == label).sum().item()

    #返回准确率
    return 100.0 * correct / total

if __name__ == "__main__":

    #训练集数据增强与预处理流水线
    train_transform = transforms.Compose([
        #先将图像缩放到 72×72
        transforms.Resize([72, 72]),
        #随机裁剪回 64×64
        transforms.RandomCrop([64, 64]),
        #以50%概率随机水平翻转图像
        transforms.RandomHorizontalFlip(p=0.5),
        #随机在 -10° ~ +10° 范围内旋转图像
        transforms.RandomRotation(degrees=(-10, 10)),
        #随机调整亮度、对比度、饱和度
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
        #将PIL图像转为张量，并把像素值从 [0,255] 缩放到 [0,1]
        transforms.ToTensor(),
        #标准化：均值0.5、标准差0.5，将数据分布拉至 [-1, 1]
        transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
    ])

    #测试集预处理流水线
    test_transform = transforms.Compose([
        #直接缩放到模型要求的 64×64
        transforms.Resize([64, 64]),
        #转为张量
        transforms.ToTensor(),
        #和训练集保持一致的标准化参数
        transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
    ])

    #批次大小(每次送入模型训练的样本数量)
    BATCH_SIZE = 128
    #最大训练轮数
    EPOCH = 200

    #加载训练集测试集，ImageFolder按文件夹自动分类，绑定预处理
    train_set = datasets.ImageFolder(root=r'dataset/train', transform=train_transform)
    test_set1 = datasets.ImageFolder(root=r'dataset/test1', transform=test_transform)
    test_set2 = datasets.ImageFolder(root=r'dataset/test2', transform=test_transform)

    #打印各个数据集的样本总数
    print(f"训练集数量: {len(train_set)}")
    print(f"测试集1数量: {len(test_set1)}")
    print(f"测试集2数量: {len(test_set2)}")

    #训练集测试集数据加载器 batch_size=BATCH_SIZE 分批读取，shuffle=True 打乱顺序 pin_memory=True 开启内存锁
    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True, pin_memory=True)
    test_loader1 = DataLoader(test_set1, batch_size=BATCH_SIZE, shuffle=True, pin_memory=True)
    test_loader2 = DataLoader(test_set2, batch_size=BATCH_SIZE, shuffle=True, pin_memory=True)

    #自动选择运行设备，有CUDA(GPU)用GPU，否则用CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    #实例化网络模型，并将模型迁移到指定设备
    net = MixedNet().to(device)
    #可视化网络结构、每层输入输出尺寸、参数量
    summary(net, input_size=(1, 3, 64, 64), device=device)
    #打印文件夹与分类标签的映射关系
    print(f"类别映射: {train_set.class_to_idx}")

    #定义损失函数 交叉熵损失
    criterion = nn.CrossEntropyLoss()
    #定义SGD随机梯度下降优化器 学习率0.01，动量0.9，L2权重衰减1e-4
    optimizer = optim.SGD(net.parameters(), lr=0.01, momentum=0.9, weight_decay=1e-4)
    #定义学习率调度器 自适应学习率调度器
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,     #绑定优化器
        mode="max",    #指标（准确率）越大越好
        factor=0.7,    #学习率衰减系数
        patience=10,   #耐心轮数
        min_lr=1e-5    #学习率下限
    )
    
    #记录目前最优准确率，初始化为0
    best_acc1 = 0.0
    #定义模型保存文件夹名称
    save_dir = "pth"
    #创建文件夹，若已存在则不报错
    os.makedirs(save_dir, exist_ok=True)
    #拼接最优模型保存路径
    best_model_path = os.path.join(save_dir, "model_best.pth")

    print("Start Training...")

    #循环遍历每一个训练轮次
    for epoch in range(EPOCH):
        #切换模型为训练模式
        net.train()
        #记录本轮所有批次的loss总和
        training_loss = 0.0

        #遍历训练集每一个批次
        for batch_id, (datas, labels) in enumerate(train_loader):
            #数据、标签迁移到对应设备
            datas, labels = datas.to(device), labels.to(device)
            #清空上一轮梯度
            optimizer.zero_grad()
            #模型前向传播，得到预测输出
            outputs = net(datas)
            #计算当前批次损失值
            loss = criterion(outputs, labels)
            #反向传播，计算各参数梯度
            loss.backward()
            #根据梯度更新网络权重参数
            optimizer.step()
            #累加当前批次loss到总loss
            training_loss += loss.item()

        #每一轮结束后，
        #scheduler.step(acc1)
        
        
        #在两个测试集上分别计算准确率
        acc1 = test_model(net, test_loader1, device)
        acc2 = test_model(net, test_loader2, device)

        #计算本轮平均损失
        avg_loss = training_loss / len(train_loader)
        #更新学习率
        scheduler.step(acc1)

        #每一个10轮
        if (epoch + 1) % 10 == 0:
            #打印本轮日志：轮数、平均损失、两个测试集准确率
            print(f"【Epoch {epoch+1:3d}】 Loss: {avg_loss:.5f} | Test1 Acc: {acc1:.2f}% | Test2 Acc: {acc2:.2f}%")

        #如果当前测试集1准确率大于历史最优
        if acc1 > best_acc1:
            #更新最优值
            best_acc1 = acc1
            #保存最优模型
            torch.save(net.state_dict(), best_model_path)

            print(f"Update best model, current highest accuracy: {best_acc1:.2f}%")

    print("Training Finished!")
    print(f"Final highest accuracy on Test Set 1: {best_acc1:.2f}%")