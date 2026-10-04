// Test stub of firebase-auth.js. Users live in window.__fbs.users = {name: {pw, role}}; the session is kept per app name in localStorage.
const S = () => window.__fbs;
const key = (app) => "__fbstub_user_" + app.name;
export function getAuth(app) {
  return {
    app,
    get currentUser() {
      const n = localStorage.getItem(key(app));
      return n ? { uid: "uid_" + n, email: n + "@mangiasassi.invalid", name: n } : null;
    },
    authStateReady: async () => {},
  };
}
export async function signInWithEmailAndPassword(auth, email, pw) {
  if (S().offline) throw { code: "auth/network-request-failed" };
  if (S().tooMany) throw { code: "auth/too-many-requests" };
  const n = email.split("@")[0], u = S().users[n];
  if (!u || u.pw !== pw) throw { code: "auth/invalid-credential" };
  localStorage.setItem(key(auth.app), n);
  return { user: auth.currentUser };
}
// L1: registration. Mirrors the SDK errors; the new user is signed in like the real one. Calls are logged in __fbs.createCalls.
export async function createUserWithEmailAndPassword(auth, email, pw) {
  const F = S();
  (F.createCalls = F.createCalls || []).push(email);
  if (F.offline) throw { code: "auth/network-request-failed" };
  if (F.tooMany) throw { code: "auth/too-many-requests" };
  const n = email.split("@")[0];
  if (F.users[n]) throw { code: "auth/email-already-in-use" };
  if (pw.length < 6) throw { code: "auth/weak-password" };
  F.users[n] = { pw, role: null };
  localStorage.setItem(key(auth.app), n);
  return { user: auth.currentUser };
}
export async function signOut(auth) { localStorage.removeItem(key(auth.app)); window.__fbs.signedOut = (window.__fbs.signedOut || 0) + 1; }
export const EmailAuthProvider = { credential: (email, pw) => ({ email, pw }) };
export async function reauthenticateWithCredential(user, cred) {
  if (S().users[user.name].pw !== cred.pw) throw { code: "auth/invalid-credential" };
}
export async function updatePassword(user, pw) { S().users[user.name].pw = pw; window.__fbs.pwSet = pw.length; }
