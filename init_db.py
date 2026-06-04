"""初始化数据库并插入丰富的测试数据，包括学习行为记录、章节、积分商城商品"""
import sys
import os
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.course import Course, Category
from app.models.learning import LearningRecord, UserCourseProgress, Enrollment
from app.models.chapter import Chapter
from app.models.mall import MallItem
from app.models.growth import PointsAccount

app = create_app()

with app.app_context():
    db.create_all()

    # 增量迁移：为已有表添加新字段
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if 'redemption_orders' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('redemption_orders')]
        if 'used_at' not in columns:
            db.session.execute(text('ALTER TABLE redemption_orders ADD COLUMN used_at DATETIME'))
            db.session.commit()

    # 如果已有用户数据，跳过种子数据插入
    if User.query.first():
        print('数据库已有数据，跳过初始化。仅执行表结构迁移(create_all)。')
        print('如需重新初始化，请手动删除 education.db 后重新运行。')
        exit(0)

    # ========== 创建用户 ==========
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)

    students = []
    student_data = [
        ('student', 'student@example.com', '123456'),
        ('zhangsan', 'zhangsan@example.com', '123456'),
        ('lisi', 'lisi@example.com', '123456'),
        ('wangwu', 'wangwu@example.com', '123456'),
        ('xiaoming', 'xiaoming@example.com', '123456'),
    ]
    for uname, email, pwd in student_data:
        u = User(username=uname, email=email, role='student')
        u.set_password(pwd)
        db.session.add(u)
        students.append(u)

    db.session.commit()

    # ========== 创建课程分类 ==========
    categories_data = [
        ('前端开发', 'HTML/CSS/JavaScript/Vue/React等前端技术课程'),
        ('后端开发', 'Python/Java/Go/Node.js等后端开发技术'),
        ('数据科学', '机器学习/深度学习/数据分析/统计学'),
        ('移动开发', 'Android/iOS/Flutter/React Native跨平台开发'),
        ('人工智能', 'NLP/计算机视觉/强化学习/大模型应用'),
        ('数据库', 'MySQL/Redis/MongoDB/PostgreSQL/数据库优化'),
        ('云计算', 'Docker/Kubernetes/AWS/微服务架构'),
        ('网络安全', '渗透测试/密码学/安全防护/CTF'),
    ]

    categories = {}
    for name, desc in categories_data:
        c = Category(name=name, description=desc)
        db.session.add(c)
        categories[name] = c

    db.session.commit()

    # ========== 创建课程 ==========
    courses_data = [
        {
            'title': 'Vue 3 从入门到精通',
            'description': '本课程系统讲解Vue 3的核心概念，包括组合式API、响应式系统、组件化开发、Pinia状态管理、Vue Router路由等，适合有JavaScript基础的开发者学习。',
            'category': '前端开发',
            'teacher_name': '张老师',
            'duration': 1200,
            'difficulty': 'intermediate',
            'price': 199.0,
            'cover_image': 'https://picsum.photos/seed/vue3/400/225'
        },
        {
            'title': 'Python Flask Web开发实战',
            'description': '从零开始学习Flask框架，构建完整的Web应用，涵盖路由、模板引擎、数据库ORM、用户认证、RESTful API设计等核心功能。',
            'category': '后端开发',
            'teacher_name': '李老师',
            'duration': 960,
            'difficulty': 'beginner',
            'price': 149.0,
            'cover_image': 'https://picsum.photos/seed/flask/400/225'
        },
        {
            'title': '机器学习入门与实践',
            'description': '系统学习机器学习基础算法，包括线性回归、逻辑回归、决策树、SVM、随机森林、XGBoost等，配合sklearn实战项目。',
            'category': '数据科学',
            'teacher_name': '王老师',
            'duration': 1800,
            'difficulty': 'intermediate',
            'price': 299.0,
            'cover_image': 'https://picsum.photos/seed/ml/400/225'
        },
        {
            'title': 'React 18 + TypeScript高级进阶',
            'description': '深入React 18新特性，包括并发模式、Suspense、Server Components、React Query、Zustand状态管理等。',
            'category': '前端开发',
            'teacher_name': '赵老师',
            'duration': 900,
            'difficulty': 'advanced',
            'price': 249.0,
            'cover_image': 'https://picsum.photos/seed/react18/400/225'
        },
        {
            'title': 'MySQL数据库从入门到优化',
            'description': '全面学习MySQL数据库，从基础SQL语法到索引原理、查询优化、事务与锁机制、主从复制、分库分表等高级话题。',
            'category': '数据库',
            'teacher_name': '陈老师',
            'duration': 1080,
            'difficulty': 'beginner',
            'price': 129.0,
            'cover_image': 'https://picsum.photos/seed/mysql/400/225'
        },
        {
            'title': '深度学习与PyTorch实战',
            'description': '基于PyTorch讲解深度学习核心概念，包括CNN、RNN、LSTM、Transformer、GAN等网络架构的原理和代码实现。',
            'category': '人工智能',
            'teacher_name': '刘老师',
            'duration': 2400,
            'difficulty': 'advanced',
            'price': 399.0,
            'cover_image': 'https://picsum.photos/seed/pytorch/400/225'
        },
        {
            'title': 'Go语言高并发编程',
            'description': '深入学习Go语言的goroutine、channel、sync包等并发编程机制，并构建高性能HTTP服务、RPC框架和消息队列。',
            'category': '后端开发',
            'teacher_name': '周老师',
            'duration': 1440,
            'difficulty': 'advanced',
            'price': 279.0,
            'cover_image': 'https://picsum.photos/seed/golang/400/225'
        },
        {
            'title': 'Flutter跨平台App开发',
            'description': '使用Flutter框架开发iOS和Android应用，掌握Dart语言、Widget体系、状态管理、网络请求、本地存储等核心技能。',
            'category': '移动开发',
            'teacher_name': '孙老师',
            'duration': 1560,
            'difficulty': 'intermediate',
            'price': 229.0,
            'cover_image': 'https://picsum.photos/seed/flutter/400/225'
        },
        {
            'title': 'JavaScript高级程序设计',
            'description': '深入理解JavaScript底层原理，包括原型链、闭包、作用域、事件循环、异步编程、模块化等核心概念。',
            'category': '前端开发',
            'teacher_name': '张老师',
            'duration': 1320,
            'difficulty': 'intermediate',
            'price': 179.0,
            'cover_image': 'https://picsum.photos/seed/javascript/400/225'
        },
        {
            'title': 'Redis缓存架构实战',
            'description': '学习Redis五大数据结构、持久化方案、哨兵集群、Redis Cluster、缓存穿透/击穿/雪崩解决方案、分布式锁实现。',
            'category': '数据库',
            'teacher_name': '吴老师',
            'duration': 720,
            'difficulty': 'intermediate',
            'price': 169.0,
            'cover_image': 'https://picsum.photos/seed/redis/400/225'
        },
        {
            'title': 'NLP自然语言处理实战',
            'description': '从文本预处理到Transformer/BERT/GPT模型，系统学习NLP技术栈，包括分词、命名实体识别、情感分析、文本生成等。',
            'category': '人工智能',
            'teacher_name': '黄老师',
            'duration': 1680,
            'difficulty': 'advanced',
            'price': 349.0,
            'cover_image': 'https://picsum.photos/seed/nlp/400/225'
        },
        {
            'title': 'HTML+CSS零基础入门',
            'description': '面向编程零基础学员，系统讲解HTML5语义化标签和CSS3布局技巧（Flex/Grid），完成个人博客、电商首页等实战项目。',
            'category': '前端开发',
            'teacher_name': '林老师',
            'duration': 600,
            'difficulty': 'beginner',
            'price': 0.0,
            'cover_image': 'https://picsum.photos/seed/htmlcss/400/225'
        },
        {
            'title': 'Docker与Kubernetes实战',
            'description': '从Docker容器化基础到Kubernetes集群编排，学习微服务部署、服务发现、自动扩缩容、CI/CD流水线搭建等云原生技术。',
            'category': '云计算',
            'teacher_name': '马老师',
            'duration': 1200,
            'difficulty': 'intermediate',
            'price': 259.0,
            'cover_image': 'https://picsum.photos/seed/docker/400/225'
        },
        {
            'title': 'Spring Boot 3微服务开发',
            'description': '基于Spring Boot 3和Spring Cloud构建微服务架构，包含服务注册发现、配置中心、网关、熔断、分布式事务等完整方案。',
            'category': '后端开发',
            'teacher_name': '郑老师',
            'duration': 1800,
            'difficulty': 'intermediate',
            'price': 269.0,
            'cover_image': 'https://picsum.photos/seed/springboot/400/225'
        },
        {
            'title': 'Python数据分析与可视化',
            'description': '使用Pandas、NumPy进行数据清洗和分析，结合Matplotlib、Seaborn、Plotly进行数据可视化，完成真实数据集分析项目。',
            'category': '数据科学',
            'teacher_name': '王老师',
            'duration': 840,
            'difficulty': 'beginner',
            'price': 99.0,
            'cover_image': 'https://picsum.photos/seed/pandas/400/225'
        },
        {
            'title': 'Web安全渗透测试入门',
            'description': '学习OWASP Top 10漏洞原理与利用，包括SQL注入、XSS、CSRF、文件上传漏洞等，配合靶场环境实操练习。',
            'category': '网络安全',
            'teacher_name': '钱老师',
            'duration': 960,
            'difficulty': 'intermediate',
            'price': 199.0,
            'cover_image': 'https://picsum.photos/seed/websec/400/225'
        },
        {
            'title': 'Node.js后端开发进阶',
            'description': '深入Node.js事件循环、流处理、集群模式，使用Express/Koa构建RESTful API，配合MongoDB和Socket.io开发实时应用。',
            'category': '后端开发',
            'teacher_name': '李老师',
            'duration': 1080,
            'difficulty': 'intermediate',
            'price': 189.0,
            'cover_image': 'https://picsum.photos/seed/nodejs/400/225'
        },
        {
            'title': '大模型应用开发实战',
            'description': '基于OpenAI API和LangChain框架开发AI应用，涵盖Prompt Engineering、RAG检索增强生成、Agent智能体、Fine-tuning等核心技术。',
            'category': '人工智能',
            'teacher_name': '刘老师',
            'duration': 1200,
            'difficulty': 'intermediate',
            'price': 329.0,
            'cover_image': 'https://picsum.photos/seed/llm/400/225'
        },
        {
            'title': 'TypeScript系统入门',
            'description': '从零学习TypeScript类型系统，包括基础类型、泛型、类型推断、装饰器、声明文件等，提升JavaScript项目的代码质量和开发效率。',
            'category': '前端开发',
            'teacher_name': '赵老师',
            'duration': 720,
            'difficulty': 'beginner',
            'price': 119.0,
            'cover_image': 'https://picsum.photos/seed/typescript/400/225'
        },
        {
            'title': 'Kotlin Android开发实战',
            'description': '使用Kotlin语言和Jetpack Compose构建现代Android应用，涵盖MVVM架构、协程、Room数据库、Retrofit网络请求等。',
            'category': '移动开发',
            'teacher_name': '孙老师',
            'duration': 1320,
            'difficulty': 'intermediate',
            'price': 219.0,
            'cover_image': 'https://picsum.photos/seed/kotlin/400/225'
        },
    ]

    courses = []
    for cd in courses_data:
        course = Course(
            title=cd['title'],
            description=cd['description'],
            category_id=categories[cd['category']].id,
            teacher_name=cd['teacher_name'],
            duration=cd['duration'],
            difficulty=cd['difficulty'],
            price=cd['price'],
            cover_image=cd['cover_image'],
            status='published',
            view_count=random.randint(50, 2000)
        )
        db.session.add(course)
        courses.append(course)

    db.session.commit()

    # ========== 创建课程章节 ==========
    print('正在生成课程章节数据...')

    for course in courses:
        chapter_count = random.randint(4, 6)
        for idx in range(1, chapter_count + 1):
            chapter = Chapter(
                course_id=course.id,
                title=f'{course.title} - 第{idx}章',
                description=f'本章介绍{course.title}的第{idx}部分核心内容',
                order_num=idx,
                duration=random.randint(15, 45),
                is_free=(idx == 1)
            )
            db.session.add(chapter)

    db.session.commit()
    print(f'  章节数: {Chapter.query.count()}')

    # ========== 创建学习行为数据 ==========
    print('正在生成学习行为数据...')

    now = datetime.utcnow()

    for student in students:
        learned_courses = random.sample(courses, random.randint(3, 8))

        for course in learned_courses:
            if course.price > 0:
                enrollment = Enrollment(
                    user_id=student.id,
                    course_id=course.id,
                    enrolled_at=now - timedelta(days=random.randint(5, 30))
                )
                db.session.add(enrollment)

            max_progress = random.choice([15, 30, 45, 60, 75, 90, 100])
            total_dur = 0
            start_time = now - timedelta(days=random.randint(1, 30))

            record_time = start_time

            record = LearningRecord(
                user_id=student.id,
                course_id=course.id,
                action='view',
                progress=0,
                duration=0,
                created_at=record_time
            )
            db.session.add(record)

            steps = random.randint(3, 8)
            progress_per_step = max_progress / steps

            for i in range(steps):
                record_time += timedelta(hours=random.randint(1, 48))
                current_progress = min(round(progress_per_step * (i + 1), 1), max_progress)
                step_duration = random.randint(120, 2700)
                total_dur += step_duration

                action = 'start' if i == 0 else ('complete' if current_progress >= 100 else 'progress')
                record = LearningRecord(
                    user_id=student.id,
                    course_id=course.id,
                    action=action,
                    progress=current_progress,
                    duration=step_duration,
                    created_at=record_time
                )
                db.session.add(record)

            status = 'completed' if max_progress >= 100 else 'learning'
            user_progress = UserCourseProgress(
                user_id=student.id,
                course_id=course.id,
                progress=max_progress,
                total_duration=total_dur,
                last_learn_at=record_time,
                status=status,
                started_at=start_time,
                completed_at=record_time if status == 'completed' else None
            )
            db.session.add(user_progress)
            course.student_count += 1

    db.session.commit()

    # ========== 创建积分账户 ==========
    print('正在初始化积分账户...')
    for student in students:
        account = PointsAccount(
            user_id=student.id,
            balance=random.randint(50, 500),
            total_earned=random.randint(100, 800),
            total_spent=random.randint(0, 200)
        )
        db.session.add(account)
    db.session.commit()

    # ========== 创建积分商城商品 ==========
    print('正在创建积分商城商品...')

    mall_items = [
        {
            'name': '课程优惠券 - 满200减50',
            'description': '购买任意课程满200元可使用，有效期30天',
            'type': 'coupon',
            'points_cost': 200,
            'stock': 100,
            'image': 'https://picsum.photos/seed/coupon1/200/200',
            'extra_data': '{"min_amount": 200, "discount": 50}'
        },
        {
            'name': '课程优惠券 - 满100减20',
            'description': '购买任意课程满100元可使用，有效期30天',
            'type': 'coupon',
            'points_cost': 100,
            'stock': 200,
            'image': 'https://picsum.photos/seed/coupon2/200/200',
            'extra_data': '{"min_amount": 100, "discount": 20}'
        },
        {
            'name': 'VIP会员 - 7天体验',
            'description': '7天VIP会员，解锁所有课程免费学习',
            'type': 'vip',
            'points_cost': 500,
            'stock': 50,
            'image': 'https://picsum.photos/seed/vip7/200/200'
        },
        {
            'name': 'VIP会员 - 30天',
            'description': '30天VIP会员，解锁所有课程免费学习',
            'type': 'vip',
            'points_cost': 1500,
            'stock': 30,
            'image': 'https://picsum.photos/seed/vip30/200/200'
        },
        {
            'name': '编程学习电子书合集',
            'description': '包含Python、JavaScript、Go等10本精选电子书',
            'type': 'resource',
            'points_cost': 300,
            'stock': -1,
            'image': 'https://picsum.photos/seed/ebook/200/200'
        },
        {
            'name': 'LeetCode题解PDF',
            'description': '精选200道高频面试题详细解析',
            'type': 'resource',
            'points_cost': 150,
            'stock': -1,
            'image': 'https://picsum.photos/seed/leetcode/200/200'
        },
        {
            'name': '定制程序员鼠标垫',
            'description': '高品质加厚鼠标垫，印有代码风格图案',
            'type': 'physical',
            'points_cost': 800,
            'stock': 20,
            'image': 'https://picsum.photos/seed/mousepad/200/200'
        },
        {
            'name': '技术主题T恤',
            'description': '纯棉材质，多种编程语言Logo可选',
            'type': 'physical',
            'points_cost': 1200,
            'stock': 15,
            'image': 'https://picsum.photos/seed/tshirt/200/200'
        },
        {
            'name': '机械键盘抽奖券',
            'description': '参与月度抽奖，有机会获得Cherry机械键盘一把',
            'type': 'physical',
            'points_cost': 50,
            'stock': 500,
            'image': 'https://picsum.photos/seed/keyboard/200/200'
        },
        {
            'name': '1对1导师答疑30分钟',
            'description': '预约资深导师进行1对1技术答疑',
            'type': 'resource',
            'points_cost': 1000,
            'stock': 10,
            'image': 'https://picsum.photos/seed/mentor/200/200'
        },
    ]

    for item_data in mall_items:
        item = MallItem(
            name=item_data['name'],
            description=item_data['description'],
            type=item_data['type'],
            points_cost=item_data['points_cost'],
            stock=item_data['stock'],
            image=item_data['image'],
            extra_data=item_data.get('extra_data', '{}')
        )
        db.session.add(item)

    db.session.commit()

    # 统计结果
    print('\n========== 数据库初始化完成 ==========')
    print(f'  用户数: {User.query.count()} (1管理员 + {len(students)}学生)')
    print(f'  分类数: {Category.query.count()}')
    print(f'  课程数: {Course.query.count()}')
    print(f'  章节数: {Chapter.query.count()}')
    print(f'  报名记录: {Enrollment.query.count()}')
    print(f'  学习进度记录: {UserCourseProgress.query.count()}')
    print(f'  学习行为记录: {LearningRecord.query.count()}')
    print(f'  积分商城商品: {MallItem.query.count()}')
    print()
    print('测试账号:')
    print('  管理员: admin / admin123')
    print('  学  生: student / 123456')
    print('        zhangsan / 123456')
    print('        lisi / 123456')
    print('        wangwu / 123456')
    print('        xiaoming / 123456')
    print()
    print('新增功能模块:')
    print('  - 学习画像: /api/profile/learning-profile')
    print('  - 风险评估: /api/profile/risk-assessment')
    print('  - 效果评估: /api/profile/effect-assessment')
    print('  - 成长体系: /api/growth/plans | /api/growth/check-in | /api/growth/points')
    print('  - 积分商城: /api/mall/items | /api/mall/redeem')
    print('  - 课程推荐: /api/recommend/')
    print('  - 运营分析: /api/analytics/realtime | /api/analytics/overview')
