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
    path: '/search',
    name: 'search',
    component: () => import('../../pages/SearchPage.vue'),
  },
  {
    // Reasoning-trace tunnel. Route is always registered; the page shows
    // an empty state when the `reasoning` feature flag is off (same pattern
    // as /search does for ingestion).
    path: '/reasoning',
    name: 'reasoning',
    component: () => import('../../pages/ReasoningPage.vue'),
  },
  {
    // Deep-link into a specific document's reasoning workspace, e.g. shared
    // by Peter to a teammate.
    path: '/reasoning/:docId',
    name: 'reasoning-doc',
    component: () => import('../../pages/ReasoningPage.vue'),
    props: true,
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
