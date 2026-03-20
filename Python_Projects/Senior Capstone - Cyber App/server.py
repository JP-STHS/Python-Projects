# =============================================================================
# CYBERAPP  —  RELAY SERVER
# =============================================================================
# A lightweight WebSocket relay that connects CyberApp users over the internet.
#
# The server is BLIND — it only sees encrypted binary blobs.
# It cannot read any messages or files. All E2E encryption happens client-side.
#
# HOW IT WORKS:
#   1. Clients connect and announce their nickname
#   2. Server broadcasts the peer list to everyone
#   3. When client A wants to chat with client B, A sends a "relay" message
#      addressed to B's connection ID — the server forwards it without reading it
#   4. The ECDH handshake and AES-256-GCM encryption happen between the two
#      clients; the server just moves the bytes
#
# DEPLOY FREE:
#   Railway  → railway up  (add a Procfile: web: python server.py)
#   Render   → connect GitHub repo, set start command: python server.py
#   Fly.io   → fly launch, fly deploy
#   Local    → python server.py  (then share your IP or use ngrok)
#
# DEPENDENCIES:
#   pip install websockets
#
# ENV VARS:
#   PORT  — override default port 8765 (Render/Railway set this automatically)
# =============================================================================

import asyncio
import json
import os
import time
import websockets
from websockets.server import WebSocketServerProtocol

# ── State ─────────────────────────────────────────────────────────────────────

# conn_id → {"ws": websocket, "nickname": str, "joined": float}
clients: dict[str, dict] = {}
_id_counter = 0

def _new_id() -> str:
    global _id_counter
    _id_counter += 1
    return f"u{_id_counter}"

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _send(ws: WebSocketServerProtocol, msg: dict):
    try:
        await ws.send(json.dumps(msg))
    except Exception:
        pass

async def _broadcast_peer_list():
    """Send the current peer list to every connected client."""
    peers = [
        {"id": cid, "nickname": info["nickname"]}
        for cid, info in clients.items()
    ]
    msg = json.dumps({"type": "peer_list", "peers": peers})
    dead = []
    for cid, info in list(clients.items()):
        try:
            await info["ws"].send(msg)
        except Exception:
            dead.append(cid)
    for cid in dead:
        clients.pop(cid, None)

# ── Handler ───────────────────────────────────────────────────────────────────

async def handle(ws: WebSocketServerProtocol):
    conn_id  = _new_id()
    nickname = f"anon_{conn_id}"
    clients[conn_id] = {"ws": ws, "nickname": nickname, "joined": time.time()}
    print(f"[+] {conn_id} connected  (total: {len(clients)})")

    # Tell the new client their assigned ID
    await _send(ws, {"type": "welcome", "your_id": conn_id})
    await _broadcast_peer_list()

    try:
        async for raw in ws:
            try:
                # All control messages are JSON text frames
                if isinstance(raw, str):
                    msg = json.loads(raw)
                    mtype = msg.get("type")

                    # ── announce: client sets their nickname ──
                    if mtype == "announce":
                        nick = str(msg.get("nickname", nickname))[:32].strip()
                        if nick:
                            clients[conn_id]["nickname"] = nick
                            print(f"    {conn_id} is now '{nick}'")
                            await _broadcast_peer_list()

                    # ── relay_text: forward a JSON message to one peer ──
                    elif mtype == "relay_text":
                        target_id = msg.get("to")
                        if target_id and target_id in clients:
                            fwd = {
                                "type":    "relay_text",
                                "from":    conn_id,
                                "from_nick": clients[conn_id]["nickname"],
                                "payload": msg.get("payload"),
                            }
                            await _send(clients[target_id]["ws"], fwd)

                    # ── ping: keepalive ──
                    elif mtype == "ping":
                        await _send(ws, {"type": "pong"})

                # Binary frames = encrypted handshake / file data, relay as-is
                elif isinstance(raw, bytes):
                    # Format: 4-byte target_id_len + target_id + encrypted_blob
                    if len(raw) < 5:
                        continue
                    tid_len = int.from_bytes(raw[:4], "big")
                    if 4 + tid_len > len(raw):
                        continue
                    target_id   = raw[4:4 + tid_len].decode()
                    blob        = raw[4 + tid_len:]
                    if target_id in clients:
                        # Prepend sender ID so receiver knows who it's from
                        sid_bytes = conn_id.encode()
                        frame     = len(sid_bytes).to_bytes(4, "big") + sid_bytes + blob
                        try:
                            await clients[target_id]["ws"].send(frame)
                        except Exception:
                            pass

            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.pop(conn_id, None)
        print(f"[-] {conn_id} disconnected  (total: {len(clients)})")
        await _broadcast_peer_list()

# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"CyberApp Relay Server  —  ws://0.0.0.0:{port}")
    print("Waiting for clients…\n")
    async with websockets.serve(handle, "0.0.0.0", port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
