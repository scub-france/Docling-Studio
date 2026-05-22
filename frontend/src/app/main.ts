import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { router } from './router'
import { useFeatureFlagStore } from '../features/feature-flags'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)

// Kick off the feature-flag load eagerly so it's typically settled by
// the time the router's beforeEach guard runs. The guard itself awaits
// the same load promise (see app/router/index.ts) — calling load()
// here is just a warm-up, not a precondition for mount. main.ts
// therefore mounts immediately; only the very first navigation may
// briefly wait for /api/health to resolve, after which the in-flight
// promise is cached and subsequent guards return synchronously.
useFeatureFlagStore().load()

app.mount('#app')
