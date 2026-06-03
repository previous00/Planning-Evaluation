import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/auth/Register.vue')
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/course/CourseList.vue')
      },
      {
        path: 'courses',
        name: 'Courses',
        component: () => import('../views/course/CourseList.vue')
      },
      {
        path: 'course/:id',
        name: 'CourseDetail',
        component: () => import('../views/course/CourseDetail.vue')
      },
      {
        path: 'course/:id/chapter/:chapterId',
        name: 'ChapterLearn',
        component: () => import('../views/course/ChapterLearn.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'learning',
        name: 'Learning',
        component: () => import('../views/learning/LearningCenter.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'recommend',
        name: 'Recommend',
        component: () => import('../views/recommend/RecommendPage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/auth/Profile.vue'),
        meta: { requiresAuth: true }
      }
    ]
  },
  {
    path: '/admin',
    component: () => import('../components/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/admin/Dashboard.vue')
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('../views/admin/UserManage.vue')
      },
      {
        path: 'courses',
        name: 'AdminCourses',
        component: () => import('../views/admin/CourseManage.vue')
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('../views/admin/CategoryManage.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.requiresAdmin && user?.role !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router
