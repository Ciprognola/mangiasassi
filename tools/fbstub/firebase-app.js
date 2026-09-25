// Test stub of firebase-app.js (tools/fbstub): no network, no real Firebase.
export function initializeApp(cfg, name) {
  (window.__fbs.apps = window.__fbs.apps || []).push(name);
  return { name, cfg };
}
