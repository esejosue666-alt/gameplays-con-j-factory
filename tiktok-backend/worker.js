/**
 * Gameplays con J — TikTok OAuth + Content Posting API (video.upload)
 * Deploy on Cloudflare Workers. Never put TikTok secrets in GitHub Pages.
 */
const API = "https://open.tiktokapis.com";

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
  });
}
function cookie(name, value, maxAge) {
  return `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}
function randomHex(bytes = 32) {
  const a = new Uint8Array(bytes); crypto.getRandomValues(a);
  return [...a].map(x => x.toString(16).padStart(2, "0")).join("");
}
async function sha256(s) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}
function getCookie(request, name) {
  const raw = request.headers.get("Cookie") || "";
  const m = raw.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
  return m ? decodeURIComponent(m[1]) : null;
}
function redirect(url, headers = {}) {
  return new Response(null, { status: 302, headers: { Location: url, ...headers } });
}
async function readSession(request, env) {
  const sid = getCookie(request, "gcj_tiktok_sid");
  if (!sid || !/^[a-f0-9]{64}$/.test(sid)) return null;
  const raw = await env.TIKTOK_KV.get("session:" + sid);
  return raw ? { sid, data: JSON.parse(raw) } : null;
}
async function refreshIfNeeded(session, env) {
  let t = session.data;
  if (Date.now() < (t.expires_at - 60_000)) return t;
  if (!t.refresh_token || Date.now() > t.refresh_expires_at) {
    throw new Error("La sesión de TikTok expiró. Vuelve a conectar tu cuenta.");
  }
  const body = new URLSearchParams({
    client_key: env.TIKTOK_CLIENT_KEY,
    client_secret: env.TIKTOK_CLIENT_SECRET,
    grant_type: "refresh_token",
    refresh_token: t.refresh_token
  });
  const r = await fetch(API + "/v2/oauth/token/", {
    method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body
  });
  const j = await r.json();
  if (!r.ok || j.error) throw new Error(j.error_description || j.error || "No se pudo renovar el token.");
  t = { ...t, access_token: j.access_token, refresh_token: j.refresh_token,
    expires_at: Date.now() + (j.expires_in * 1000),
    refresh_expires_at: Date.now() + (j.refresh_expires_in * 1000) };
  await env.TIKTOK_KV.put("session:" + session.sid, JSON.stringify(t), { expirationTtl: 60 * 60 * 24 * 180 });
  return t;
}
async function startOAuth(request, env) {
  const sid = randomHex();
  const state = randomHex();
  await env.TIKTOK_KV.put("state:" + sid, state, { expirationTtl: 600 });
  const callback = env.TIKTOK_REDIRECT_URI;
  const u = new URL("https://www.tiktok.com/v2/auth/authorize/");
  u.searchParams.set("client_key", env.TIKTOK_CLIENT_KEY);
  u.searchParams.set("response_type", "code");
  u.searchParams.set("scope", "user.info.basic,video.upload");
  u.searchParams.set("redirect_uri", callback);
  u.searchParams.set("state", state);
  return redirect(u.toString(), { "Set-Cookie": cookie("gcj_tiktok_sid", sid, 600) });
}
async function oauthCallback(request, env) {
  const u = new URL(request.url);
  const sid = getCookie(request, "gcj_tiktok_sid");
  const state = u.searchParams.get("state");
  const expected = sid ? await env.TIKTOK_KV.get("state:" + sid) : null;
  if (!sid || !expected || !state || state !== expected) return json({ error: "Validación de seguridad fallida. Intenta conectar de nuevo." }, 400);
  await env.TIKTOK_KV.delete("state:" + sid);
  if (u.searchParams.get("error")) return json({ error: u.searchParams.get("error_description") || u.searchParams.get("error") }, 400);
  const code = u.searchParams.get("code");
  if (!code) return json({ error: "TikTok no devolvió el código de autorización." }, 400);
  const body = new URLSearchParams({
    client_key: env.TIKTOK_CLIENT_KEY,
    client_secret: env.TIKTOK_CLIENT_SECRET,
    code,
    grant_type: "authorization_code",
    redirect_uri: env.TIKTOK_REDIRECT_URI
  });
  const r = await fetch(API + "/v2/oauth/token/", {
    method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body
  });
  const j = await r.json();
  if (!r.ok || j.error) return json({ error: j.error_description || j.error || "TikTok rechazó el intercambio de token." }, 400);
  const session = {
    access_token: j.access_token, refresh_token: j.refresh_token, open_id: j.open_id,
    scope: j.scope || "", expires_at: Date.now() + j.expires_in * 1000,
    refresh_expires_at: Date.now() + j.refresh_expires_in * 1000
  };
  await env.TIKTOK_KV.put("session:" + sid, JSON.stringify(session), { expirationTtl: 60 * 60 * 24 * 180 });
  return redirect(env.APP_URL + "?tiktok=connected", { "Set-Cookie": cookie("gcj_tiktok_sid", sid, 60 * 60 * 24 * 180) });
}
async function status(request, env) {
  const s = await readSession(request, env);
  if (!s) return json({ connected: false });
  try {
    const t = await refreshIfNeeded(s, env);
    return json({ connected: true, scopes: t.scope, open_id: t.open_id });
  } catch (e) { return json({ connected: false, error: e.message }, 401); }
}
async function upload(request, env) {
  const s = await readSession(request, env);
  if (!s) return json({ error: "Primero conecta tu cuenta de TikTok." }, 401);
  let token;
  try { token = await refreshIfNeeded(s, env); }
  catch (e) { return json({ error: e.message }, 401); }
  const form = await request.formData();
  const file = form.get("video");
  if (!(file instanceof File)) return json({ error: "Selecciona un archivo de video." }, 400);
  if (file.size < 1 || file.size > 50 * 1024 * 1024) return json({ error: "El video debe pesar como máximo 50 MB para esta versión." }, 413);
  const mime = file.type || "video/mp4";
  if (!["video/mp4", "video/quicktime", "video/webm"].includes(mime)) return json({ error: "Formato no compatible. Usa MP4, MOV o WebM." }, 400);
  const size = file.size;
  const chunkSize = size <= 64 * 1024 * 1024 ? size : 64 * 1024 * 1024;
  const count = Math.floor(size / chunkSize);
  const init = await fetch(API + "/v2/post/publish/inbox/video/init/", {
    method: "POST",
    headers: { Authorization: "Bearer " + token.access_token, "Content-Type": "application/json; charset=UTF-8" },
    body: JSON.stringify({ source_info: { source: "FILE_UPLOAD", video_size: size, chunk_size: chunkSize, total_chunk_count: count } })
  });
  const initData = await init.json();
  if (!init.ok || initData.error?.code !== "ok" || !initData.data?.upload_url) {
    return json({ error: initData.error?.message || "TikTok no pudo iniciar la carga.", details: initData.error?.code }, 502);
  }
  const bytes = new Uint8Array(await file.arrayBuffer());
  let offset = 0;
  while (offset < size) {
    const endExclusive = Math.min(offset + chunkSize, size);
    const part = bytes.slice(offset, endExclusive);
    const put = await fetch(initData.data.upload_url, {
      method: "PUT",
      headers: { "Content-Type": mime, "Content-Length": String(part.byteLength),
        "Content-Range": `bytes ${offset}-${endExclusive - 1}/${size}` },
      body: part
    });
    if (![200, 201, 206].includes(put.status)) {
      return json({ error: "TikTok rechazó una parte del video.", http_status: put.status }, 502);
    }
    offset = endExclusive;
  }
  return json({ success: true, publish_id: initData.data.publish_id,
    message: "Video enviado a TikTok. Abre TikTok y revisa la notificación de la bandeja de entrada para terminar de publicarlo." });
}
async function disconnect(request, env) {
  const s = await readSession(request, env);
  if (s) {
    try {
      const t = await refreshIfNeeded(s, env);
      await fetch(API + "/v2/oauth/revoke/", { method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ client_key: env.TIKTOK_CLIENT_KEY, client_secret: env.TIKTOK_CLIENT_SECRET, token: t.access_token })
      });
    } catch (_) {}
    await env.TIKTOK_KV.delete("session:" + s.sid);
  }
  return json({ disconnected: true }, 200, { "Set-Cookie": cookie("gcj_tiktok_sid", "", 0) });
}
export default {
  async fetch(request, env) {
    const u = new URL(request.url);
    const cors = { "Access-Control-Allow-Origin": new URL(env.APP_URL).origin, "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Allow-Methods": "GET,POST", "Vary": "Origin" };\n    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    if (u.pathname === "/health") return json({ ok: true, service: "Gameplays con J TikTok bridge" });
    if (u.pathname === "/oauth/start" && request.method === "GET") return startOAuth(request, env);
    if (u.pathname === "/oauth/callback" && request.method === "GET") return oauthCallback(request, env);
    if (u.pathname === "/api/status" && request.method === "GET") return status(request, env);
    if (u.pathname === "/api/upload" && request.method === "POST") return upload(request, env);
    if (u.pathname === "/api/disconnect" && request.method === "POST") return disconnect(request, env);
    return json({ error: "Not found" }, 404);
  }
};
