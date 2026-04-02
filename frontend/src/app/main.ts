import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { router } from './router'
import { useFeatureFlagStore } from '../features/feature-flags'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.use(router)

const featureFlags = useFeatureFlagStore()
featureFlags.load()

app.mount('#app')
