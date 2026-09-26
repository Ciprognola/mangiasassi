// Test stub of firebase-firestore.js: devs/{uid}.role, bugs/edits (addDoc), saves/{docId} (F2b: getDoc + runTransaction).
export function getFirestore(app) { return { app }; }
export function doc(db, col, id) { return { db, col, id }; }
// F2b: saves live in localStorage "__fbstub_saves" = {docId: {data, rev, ts(ms), ver}} so they survive reloads; checked like firestore.rules.
const SV = () => { try { return JSON.parse(localStorage.getItem("__fbstub_saves") || "{}"); } catch (e) { return {}; } };
const SVW = (o) => localStorage.setItem("__fbstub_saves", JSON.stringify(o));
const snap = (x) => ({ exists: () => !!x, data: () => x ? Object.assign({}, x, { ts: { toMillis: () => x.ts } }) : undefined });
function saveGate(ref) {
  const S = window.__fbs;
  S.saveCalls = (S.saveCalls || 0) + 1;
  (S.saveDocs = S.saveDocs || []).push(ref.id);
  if (S.denySaves) throw { code: "permission-denied" };
  if (S.offline) throw { code: "unavailable" };
  const n = localStorage.getItem("__fbstub_user_" + ref.db.app.name);
  if (!n || (ref.id !== "uid_" + n && ref.id !== "uid_" + n + "_dev")) throw { code: "permission-denied" };  // mine()
}
export async function runTransaction(db, fn) {
  const writes = [];
  const tx = {
    async get(ref) { saveGate(ref); return snap(SV()[ref.id] || null); },
    set(ref, data) { writes.push([ref, data]); },
  };
  const r = await fn(tx);
  const all = SV();
  for (const [ref, d] of writes) {  // ok() + create/update rev rules
    const old = all[ref.id];
    const keysOk = Object.keys(d).every((k) => ["data", "rev", "ts", "ver"].includes(k));
    if (!keysOk || typeof d.data !== "string" || d.data.length > 900000 || typeof d.ver !== "string" || !(d.ts && d.ts.__ts)) throw { code: "permission-denied" };
    if (old ? d.rev !== old.rev + 1 : d.rev !== 1) throw { code: "permission-denied" };
    all[ref.id] = { data: d.data, rev: d.rev, ts: Date.now(), ver: d.ver };
    window.__fbs.saveWrites = (window.__fbs.saveWrites || 0) + 1;
  }
  SVW(all);
  return r;
}
export async function getDoc(ref) {
  if (ref.col === "saves") { saveGate(ref); return snap(SV()[ref.id] || null); }
  if (window.__fbs.offline) throw { code: "unavailable" };
  const u = window.__fbs.users[ref.id.replace("uid_", "")];
  return { exists: () => !!(u && u.role), data: () => ({ role: u.role }) };
}
// F6a: bugs collection. Writes are validated like firestore.rules (allowed keys, text 1..1000) and stored in window.__fbs.bugs.
export function collection(db, name) { return { name }; }
export function serverTimestamp() { return { __ts: true }; }
export async function addDoc(col, data) {
  const S = window.__fbs;
  if (S.denyBugs) throw { code: "permission-denied" };
  if (S.hangBugs) return new Promise(() => {});
  if (S.offline) throw { code: "unavailable" };
  if (col.name === "edits") {  // F3b: same checks as the `edits` rules
    const okKeys = ["uid", "acct", "kind", "char", "screen", "target", "locator", "before", "value", "note", "base", "ts", "meta"];
    if (Object.keys(data).some((k) => !okKeys.includes(k)) || !["text", "colour", "scale"].includes(data.kind) || typeof data.value !== "string" || data.value.length > 500 ||
        ("note" in data && (typeof data.note !== "string" || data.note.length > 300))) throw { code: "permission-denied" };
    (S.edits = S.edits || []).push(JSON.parse(JSON.stringify(data)));
    return { id: "e" + S.edits.length };
  }
  const allowed = ["uid", "text", "screen", "version", "char", "ts", "ua", "meta"];
  const keys = Object.keys(data);
  if (col.name !== "bugs" || keys.some((k) => !allowed.includes(k)) || typeof data.text !== "string" || !data.text.length || data.text.length > 1000) throw { code: "permission-denied" };
  (S.bugs = S.bugs || []).push(JSON.parse(JSON.stringify(data)));
  return { id: "b" + S.bugs.length };
}
