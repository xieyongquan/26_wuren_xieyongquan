%% 第二问：轨迹跟踪
clear; clc; close all

% 车辆参数
lfr = 2.168 + 1.907; % 轴距 L
dt = 0.01;
v = 15; 
sim_steps = 2000;
lf = 2.168;
lr = 1.907;
vx = v;

Iz = 5633.44; % 横摆转动惯量
Cf = 100000;  % 前轮侧偏刚度
Cr = 100000;  % 后轮侧偏刚度
m = 1500;     % 车辆质量

% 参考轨迹 (正弦曲线)
X_ref = 0:0.1:200; 
Y_ref = 10 * sin(X_ref / 15); 

% 初始车辆状态 
X = X_ref(1); Y = Y_ref(1) + 3; phi = 0; 
x_dot = v; y_dot = 0; phi_dot = 0;
X_vec = zeros(1, sim_steps); Y_vec = zeros(1, sim_steps);

for ii = 1:sim_steps
    X_vec(ii) = X; Y_vec(ii) = Y;
   
    % ===============================================================
    
    % ================= TODO 2.1: 实现某种跟踪算法 =================
    
    % 纯跟踪算法
    % 前瞻距离
    Ld = 11;
    % 只保留车辆前方的参考轨迹点
    idxf = X_ref > X;
    X_reff = X_ref(idxf);
    Y_reff = Y_ref(idxf);
    if isempty(X_reff)
        break;
    end
    % 最接近前瞻距离的参考轨迹点
    dist = sqrt((X_reff - X).^2 + (Y_reff - Y).^2);
    [~, idx] = min(abs(dist - Ld));
    x_Ld = X_reff(idx);
    y_Ld = Y_reff(idx);
    % 轴向和该参考轨迹点夹角
    alpha = atan2(y_Ld - Y, x_Ld - X) - phi;
    % 前轮转角
    sigma = atan( 2 * lfr * sin(alpha) / Ld );

    % ===============================================================

    % ================= TODO 2.2: 车辆状态更新 =================
    % 提示: 将刚才求得的转向角 sigma 代入运动学模型（复用第一问代码），更新 X, Y, phi。
    
    alpha_f = sigma - (y_dot + lf * phi_dot) / x_dot;
    alpha_r = - (y_dot - lr * phi_dot) / x_dot;

    Fyf = Cf * alpha_f;
    Fyr = Cr * alpha_r;
    
    y_ddot = (Fyf + Fyr) / m - x_dot * phi_dot;
    phi_ddot = (lf * Fyf - lr * Fyr) / Iz;
    
    y_dot = y_dot + y_ddot * dt;
    phi_dot = phi_dot + phi_ddot * dt;
    phi = phi + phi_dot * dt;
    
    X = X + (x_dot * cos(phi) - y_dot * sin(phi)) * dt;
    Y = Y + (x_dot * sin(phi) + y_dot * cos(phi)) * dt;
    
    % ===============================================================
    
    % 到达终点提前结束
    if X >= X_ref(end)
        break; 
    end
end

% 绘图对比
figure; hold on; grid on;
plot(X_ref, Y_ref, 'k--', 'LineWidth', 2);
plot(X_vec(1:ii), Y_vec(1:ii), 'r-', 'LineWidth', 2);
legend('参考规划轨迹', '实际行驶轨迹');
title(['Pure Pursuit 跟踪 (Ld = ', num2str(Ld), 'm)']);
xlabel('X [m]'); ylabel('Y [m]'); axis equal;