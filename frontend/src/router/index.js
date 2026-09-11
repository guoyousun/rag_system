import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { public: true, title: '注册' }
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('../views/ChatView.vue'),
        meta: { title: '智能问答' }
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('../views/DocumentsView.vue'),
        meta: { title: '文档管理' }
      },
      {
        path: 'kg',
        name: 'KG',
        component: () => import('../views/KGView.vue'),
        meta: { title: '知识图谱' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/ProfileView.vue'),
        meta: { title: '个人中心' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：未登录跳登录页
router.beforeEach((to) => {
  const userStore = useUserStore()
  if (!to.meta.public && !userStore.token) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }
  if (to.meta.public && userStore.token) {
    return { name: 'Chat' }
  }
  document.title = to.meta.title ? `${to.meta.title} · 多模式智能问答` : '多模式智能问答'
})

export default router
