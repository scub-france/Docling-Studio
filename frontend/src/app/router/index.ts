import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('../../pages/HomePage.vue'),
  },
  {
    path: '/studio',
    name: 'studio',
    component: () => import('../../pages/StudioPage.vue'),
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('../../pages/HistoryPage.vue'),
  },
  {
    path: '/documents',
    name: 'documents',
    component: () => import('../../pages/DocumentsPage.vue'),
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../../pages/SettingsPage.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
