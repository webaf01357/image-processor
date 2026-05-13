export async function onRequest(context) {
  const { request } = context; // envは一旦外す
  const url = new URL(request.url);
  
  // ⚠️ ここに直接GASのURLを一時的に書き込みます（強制突破用）
  const gasUrl = "https://script.google.com/macros/s/AKfycbzOs2S7Cuc0TS4ds4ECBK8X3lufVPHYxiPWCUTw0DuUvtcjNrX3cGqoN5wnb9wk7VhQ/exec";

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
