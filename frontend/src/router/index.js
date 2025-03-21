import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/forecasts',
    name: 'Forecasts',
    component: () => import('../views/Forecasts.vue')
  },
  {
    path: '/data-processing',
    name: 'DataProcessing',
    component: () => import('../views/DataProcessing.vue')
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('../views/Products.vue')
  },
  {
    path: '/sales',
    name: 'Sales',
    component: () => import('../views/Sales.vue')
  },
  {
    path: '/replenishments',
    name: 'Replenishments',
    component: () => import('../views/Replenishments.vue')
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router