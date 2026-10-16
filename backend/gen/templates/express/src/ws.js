// Live updates. Clients connect to /ws, then must send {"type":"auth","token":"<access token>"} within 5 s (when the app has sign-in).
// The server pushes {"type":"change","entity":"Order","op":"update"}; clients refetch over the normal, authorised REST API.
const { WebSocketServer } = require('ws');
const cfg = require('./config');
const schema = require('./schema');
const events = require('./lib/events');
const { verifyToken } = require('./middleware/auth');

function attach(server) {
  const wss = new WebSocketServer({
    server, path: '/ws', maxPayload: 2048,
    verifyClient: ({ origin }, done) => (!origin || cfg.corsOrigins.includes(origin) ? done(true) : done(false, 403, 'Origin not allowed')),
  });
  const onChange = (msg) => {
    const text = JSON.stringify({ type: 'change', ...msg });
    for (const c of wss.clients) if (c.readyState === 1 && c.authed) c.send(text);
  };
  events.on('change', onChange);
  wss.on('connection', (ws) => {
    if (wss.clients.size > cfg.wsMaxClients) return ws.close(1013, 'busy');
    ws.authed = !schema.auth;
    ws.alive = true;
    ws.on('pong', () => { ws.alive = true; });
    const timer = schema.auth ? setTimeout(() => { if (!ws.authed) ws.close(4401, 'auth required'); }, 5000) : null;
    ws.on('message', (raw) => {
      if (ws.authed) return;
      try {
        const m = JSON.parse(raw.toString());
        if (m.type === 'auth' && verifyToken(m.token)) { ws.authed = true; return ws.send('{"type":"ready"}'); }
      } catch (e) { /* fall through */ }
      return ws.close(4401, 'invalid token');
    });
    ws.on('close', () => timer && clearTimeout(timer));
  });
  const beat = setInterval(() => {
    for (const c of wss.clients) { if (!c.alive) { c.terminate(); continue; } c.alive = false; c.ping(); }
  }, 30000);
  wss.on('close', () => { clearInterval(beat); events.off('change', onChange); });
  return wss;
}

module.exports = { attach };
