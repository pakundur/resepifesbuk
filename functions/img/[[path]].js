/**
 * Cloudflare Pages Function — proxies /img/* to the R2 bucket.
 *
 * Why: img.resepifesbuk.com is a separate subdomain. Some clients/resolvers
 * fail to resolve it (NXDOMAIN) even though public DNS is correct. Serving
 * images from the main domain removes that failure mode entirely.
 *
 * Route: https://resepifesbuk.com/img/<slug>.jpg  ->  R2 key <slug>.jpg
 *
 * Free tier: Pages Functions are included in Pages; static requests are
 * unlimited. No separate Workers quota is consumed for normal traffic.
 */
export async function onRequest(context) {
  const { request, env, params } = context;
  const url = new URL(request.url);

  // params.path may be array ([[path]]) or string
  let key = params && params.path;
  if (Array.isArray(key)) key = key.join("/");

  // Fallback: derive from URL if param binding is absent
  if (!key) {
    key = url.pathname.replace(/^\/img\//, "");
  }

  if (!key) {
    return new Response("Not found", { status: 404 });
  }

  // Only allow safe, cacheable image extensions
  const ok = /\.(jpe?g|png|webp|gif|avif|svg)$/i.test(key);
  if (!ok) {
    return new Response("Forbidden", { status: 403 });
  }

  // Reject traversal attempts
  if (key.includes("..") || key.startsWith("/")) {
    return new Response("Bad request", { status: 400 });
  }

  // HEAD: answer cheaply from R2 metadata
  const isHead = request.method === "HEAD";

  const obj = await env.R2_BUCKET.get(key);
  if (obj === null) {
    return new Response("Not found", { status: 404 });
  }

  const headers = new Headers();
  obj.writeHttpMetadata(headers);
  headers.set("etag", obj.httpEtag);
  headers.set("Cache-Control", "public, max-age=31536000, immutable");
  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Access-Control-Allow-Origin", "*");

  if (isHead) {
    headers.set("Content-Length", String(obj.size));
    return new Response(null, { status: 200, headers });
  }

  return new Response(obj.body, { status: 200, headers });
}
