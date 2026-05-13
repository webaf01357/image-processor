export async function onRequest(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  
  // Cloudflareの環境変数からGASのURLを取得
  const gasUrl = env.GAS_URL;
  if (!gasUrl) {
    return new Response(JSON.stringify({ error: "GAS_URLが設定されていません" }), { status: 500 });
  }

  const targetUrl = new URL(gasUrl);
  targetUrl.search = url.search;

  try {
    const response = await fetch(targetUrl, {
      method: request.method,
      body: request.method === 'POST' ? await request.text() : null,
      headers: {
        'Content-Type': request.headers.get('Content-Type') || 'text/plain'
      }
    });

    const data = await response.text();

    return new Response(data, {
      headers: {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}
