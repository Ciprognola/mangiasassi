// Test stub of firebase-firestore.js: only devs/{uid}.role is served.
export function getFirestore(app) { return { app }; }
export function doc(db, col, id) { return { col, id }; }
export async function getDoc(ref) {
  if (window.__fbs.offline) throw { code: "unavailable" };
  const u = window.__fbs.users[ref.id.replace("uid_", "")];
  return { exists: () => !!(u && u.role), data: () => ({ role: u.role }) };
}
