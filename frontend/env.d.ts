/// <reference types="vite/client" />

declare const __APP_VERSION__: string

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, unknown>, Record<string, unknown>, unknown>
  export default component
}

// Cytoscape plugins we use in GraphView — they ship no types. Treated as
// opaque plugin objects; the runtime APIs they add to `cy` are called via
// `(cy as any)` at the call site and typed loosely.
declare module 'cytoscape-expand-collapse'
declare module 'cytoscape-navigator'
declare module 'cytoscape-navigator/cytoscape.js-navigator.css'
