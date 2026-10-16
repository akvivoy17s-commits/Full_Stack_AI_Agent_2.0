// Live updates. Clients connect to /ws, then must send {"type":"auth","token":"<access token>"} within 5 s (when the app has sign-in).
// The server pushes {"type":"change","entity":"Order","op":"update"}; clients refetch over the normal, authorised REST API.
import type { Server } from 'http';
import * as jwt from 'jsonwebtoken';
import { WebSocket, WebSocketServer } from 'ws';
import { cfg } from '../config';
import { SCHEMA } from '../schema';
import { events } from './events';

type Sock = WebSocket & { authed?: boolean; alive?: boolean };

export function attachWs(server: Server): WebSocketServer {
  const wss = new WebSocketServer({
    server, path: '/ws', maxPayload: 2048,
    verifyClient: ({ origin }: { origin?: string }, done: (ok: boolean, code?: number, msg?: string) => void) =>
      (!origin || cfg.corsOrigins.includes(origin) ? done(true) : done(false, 403, 'Origin not allowed')),
  });
  const onChange = (msg: object) => {
    const text = JSON.stringify({ type: 'change', ...msg });
    wss.clients.forEach((c: Sock) => { if (c.readyState === WebSocket.OPEN && c.authed) c.send(text); });
  };
  events.on('change', onChange);
  wss.on('connection', (ws: Sock) => {
    if (wss.clients.size > cfg.wsMaxClients) return ws.close(1013, 'busy');
    ws.authed = !SCHEMA.auth;
    ws.alive = true;
    ws.on('pong', () => { ws.alive = true; });
    const timer = SCHEMA.auth ? setTimeout(() => { if (!ws.authed) ws.close(4401, 'auth required'); }, 5000) : null;
    ws.on('message', (raw) => {
      if (ws.authed) return;
      try {
        const m = JSON.parse(raw.toString());
        if (m.type === 'auth') {
          jwt.verify(String(m.token), cfg.jwt.key, { algorithms: ['HS256'] });
          ws.authed = true;
          return ws.send('{"type":"ready"}');
        }
      } catch { /* fall through */ }
      return ws.close(4401, 'invalid token');
    });
    ws.on('close', () => { if (timer) clearTimeout(timer); });
  });
  const beat = setInterval(() => {
    wss.clients.forEach((c: Sock) => { if (!c.alive) return c.terminate(); c.alive = false; c.ping(); });
  }, 30000);
  wss.on('close', () => { clearInterval(beat); events.off('change', onChange); });
  return wss;
}
