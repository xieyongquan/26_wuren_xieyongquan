% 构造二次规划矩阵
P = sparse([1 0; 0 10]); % 二次项系数矩阵
q = [-3; -30];           % 一次项系数矩阵
A = sparse([1 1]);       % 约束方程系数矩阵
l = -inf;                % 约束下界
u = 4;                   % 约束上界

% 创建求解器对象
solver = osqp;

% 获取默认配置
settings = solver.default_settings();

% 加载问题
solver.setup(P, q, A, l, u, settings);

% 求解
res = solver.solve();

fprintf('x = %.6f\n', res.x(1));
fprintf('y = %.6f\n', res.x(2));
fprintf('μ = %.6f\n', res.y(1));
