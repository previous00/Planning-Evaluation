# 在线教育与智能推荐系统

## 技术栈
- **后端**: Flask + SQLAlchemy + Flask-JWT-Extended
- **前端**: Vue 3 + Element Plus + Pinia + Vue Router
- **数据库**: SQLite
- **构建工具**: Vite

## 项目结构
```
online_recommend/
├── venv/           # Python虚拟环境
├── backend/        # Flask后端
│   ├── app/        # 应用代码
│   │   ├── models/ # 数据模型
│   │   ├── routes/ # API路由
│   │   └── utils/  # 工具函数
│   ├── init_db.py  # 数据库初始化脚本
│   └── run.py      # 启动入口
└── frontend/       # Vue 3前端
    └── src/
        ├── api/    # API请求
        ├── views/  # 页面组件
        ├── store/  # 状态管理
        └── router/ # 路由配置
```

## 快速启动

### 1. 初始化数据库（首次运行）
```bash
cd backend
../venv/Scripts/python init_db.py
```

### 2. 启动后端服务
```bash
cd backend
../venv/Scripts/python run.py
```
后端运行在 http://localhost:5000

### 3. 启动前端开发服务器
```bash
cd frontend
npm run dev
```
前端运行在 http://localhost:3000

## 测试账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 学生 | student | 123456 |

## 功能模块

### 用户模块
- 注册/登录（JWT身份验证）
- 个人信息管理
- 角色权限控制（admin/student）

### 课程模块
- 课程列表（分页、分类筛选、关键词搜索、排序）
- 课程详情展示
- 课程管理（新增/编辑/删除 - 管理员）

### 学习行为记录
- 课程浏览记录
- 学习进度跟踪
- 学习历史查看
- 最近学习课程
- 学习统计数据

### 后台管理
- 数据仪表盘
- 用户管理
- 课程管理
- 分类管理
- 学习数据统计

## API接口

### 认证 `/api/auth`
- POST `/register` - 注册
- POST `/login` - 登录
- GET `/profile` - 获取用户信息
- PUT `/profile` - 更新用户信息

### 课程 `/api/courses`
- GET `/` - 课程列表（支持分页、筛选）
- GET `/:id` - 课程详情
- POST `/` - 新增课程
- PUT `/:id` - 编辑课程
- DELETE `/:id` - 删除课程
- GET `/categories` - 分类列表

### 学习 `/api/learning`
- POST `/record` - 记录学习行为
- GET `/progress` - 学习进度
- GET `/history` - 学习历史
- GET `/recent` - 最近学习
- GET `/stats` - 学习统计

### 管理 `/api/admin`
- GET `/dashboard` - 仪表盘数据
- GET/PUT/DELETE `/users` - 用户管理
- POST/PUT/DELETE `/categories` - 分类管理
