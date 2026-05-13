export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // ① もしブラウザが「/api/gas」宛に通信してきたら、GASへ中継する
    if (url.pathname.startsWith('/api/gas')) {
      // 一旦強制突破のため、GASのURLを直接書き込みます
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
        
        // CORS許可証をつけてブラウザに返す
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

    // ② それ以外の通信（index.htmlや画像など）は、今まで通り表示する
    return env.ASSETS.fetch(request);
  }
};
