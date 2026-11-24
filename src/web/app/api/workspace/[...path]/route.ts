const base = process.env.PARSER_API_URL ?? "http://127.0.0.1:8000";

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  if (path.join("/") === "auth/setup" && !["localhost", "127.0.0.1", "[::1]"].includes(new URL(request.url).hostname)) {
    return Response.json({ detail: "A criação inicial deve ser feita localmente." }, { status: 403 });
  }
  if (path.some((part) => !/^[a-zA-Z0-9-]+$/.test(part))) return new Response(null, { status: 400 });
  if (!["GET", "HEAD"].includes(request.method)) {
    const origin = request.headers.get("origin");
    const serverUrl = new URL(request.url);
    const allowedOrigins = new Set([serverUrl.origin]);
    // Next may normalize a loopback request to localhost internally.
    // Accept only explicit loopback aliases on the same protocol and port.
    if (["localhost", "127.0.0.1", "[::1]"].includes(serverUrl.hostname)) {
      for (const hostname of ["localhost", "127.0.0.1", "[::1]"]) {
        const localUrl = new URL(serverUrl.origin);
        localUrl.hostname = hostname;
        allowedOrigins.add(localUrl.origin);
      }
    }
    if (origin && !allowedOrigins.has(origin)) {
      return Response.json({ detail: "Origem da solicitação não autorizada." }, { status: 403 });
    }
  }
  const headers = new Headers();
  for (const key of ["cookie", "content-type", "range"]) {
    const value = request.headers.get(key);
    if (value) headers.set(key, value);
  }
  try {
    const upstream = await fetch(new URL(`/workspace/${path.join("/")}${new URL(request.url).search}`, base), {
      method: request.method, headers, cache: "no-store",
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
      signal: AbortSignal.timeout(300000),
    });
    const responseHeaders = new Headers({ "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
    for (const key of ["content-type", "content-disposition", "content-range", "accept-ranges", "set-cookie"]) {
      const value = upstream.headers.get(key);
      if (value) responseHeaders.set(key, value);
    }
    return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json({ detail: "Não foi possível acessar o servidor. Tente novamente; os dados salvos permanecem no histórico." }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
