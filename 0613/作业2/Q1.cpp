#include <iostream>
#include <eigen3/Eigen/Dense>
#include <cmath>

using namespace Eigen;
using namespace std;

// 代价函数
double cost(const Vector2d& X)
{
    double x = X(0);
    double y = X(1);
    return 0.5 * pow(x - 3, 2) + 5 * pow(y - 3, 2);
}

// 梯度函数
Vector2d grad(const Vector2d& X)
{
    Vector2d g;
    g(0) = X(0) - 3;
    g(1) = 10 * (X(1) - 3);
    return g;
}

int main()
{
    // 初始化参数
    Vector2d X(0.0, 0.0);       // 初始位置 
    const Vector2d target(3,3); // 目标位置
    double  n = 0.1;            // 学习率
    const double minerr = 1e-3; // 收敛误差
    int i = 0;                  // 迭代次数

    // 梯度下降循环
    while (true)
    {
        double err = (X - target).norm(); // 当前与目标之间距离
        if (err < minerr) 
            break;
        Vector2d g = grad(X);
        X = X - n * g;
        i++;
    }

    cout << "学习率：" << n << endl;
    cout << "迭代次数：" << i << endl;
    cout << "最终位置：" << X.transpose() << endl;
    cout << "最终误差：" << (X - target).norm() << endl;

    return 0;
}
