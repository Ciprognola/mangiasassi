// Test stub of firebase-firestore.js: only devs/{uid}.role is served.
export function getFirestore(app) { return { app }; }
export function doc(db, col, id) { return { col, id }; }
export async function getDoc(ref) {
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
