# DEPENDENCIES:
#   pip install cryptography Pillow

import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from PIL import Image, ImageTk
import os, socket, threading, json, time, struct, base64, secrets
from pathlib import Path
from datetime import datetime

# Cryptography library (pip install cryptography)
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── Constants ─────────────────────────────────────────────────────────────────
DARK_BG   = "#05053B"
DARK_MID  = "#0D0D5A"
ACCENT    = "#22B9FF"
TEAL      = "#2D5961"
TEXT_FG   = "#E0F7FF"

FONT_MAIN = ("Consolas", 13)
FONT_BIG  = ("Consolas", 20, "bold")
FONT_SM   = ("Consolas", 11)

DISCOVERY_PORT     = 55555
CHAT_PORT          = 55556
BROADCAST_INTERVAL = 3

# Where received files are saved locally
STORAGE_DIR = Path.home() / "CyberApp" / "received"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# ── Cryptographic primitives ──────────────────────────────────────────────────

def generate_keypair():
    """
    Generate a fresh X25519 keypair.
    X25519 is an elliptic curve used for Diffie-Hellman key exchange.
    It's the same curve used by Signal, WhatsApp, and WireGuard.
    Returns (private_key, public_key_bytes)
    """
    priv      = X25519PrivateKey.generate()
    pub_bytes = priv.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw
    )
    return priv, pub_bytes


def derive_session_key(private_key, peer_pub_bytes: bytes) -> bytes:
    """
    Perform ECDH and derive a symmetric AES key.

    Steps:
    1. ECDH: Combine our private key with peer's public key to get a
       'shared secret'. Both sides get the same secret without ever
       transmitting it directly.

    2. HKDF: The raw ECDH output isn't ideal as a key. HKDF (HMAC-based
       Key Derivation Function) with SHA-256 hashes it into a proper
       uniform 32-byte AES key.
    """
    peer_pub = X25519PublicKey.from_public_bytes(peer_pub_bytes)
    shared   = private_key.exchange(peer_pub)
    key      = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"cyberapp-v3-session"
    ).derive(shared)
    return key


def encrypt(key: bytes, plaintext: bytes) -> bytes:
    """
    Encrypt with AES-256-GCM (Galois/Counter Mode).

    GCM is an AEAD cipher — it provides:
      - Confidentiality: nobody can read the message
      - Integrity:       any tampering is detected (authentication tag)

    We generate a fresh random 12-byte nonce for every message.
    Reusing a nonce with the same key would be catastrophic — this is
    why we use secrets.token_bytes() (cryptographically secure random).

    Output format: nonce(12 bytes) + ciphertext
    """
    nonce = secrets.token_bytes(12)
    ct    = AESGCM(key).encrypt(nonce, plaintext, None)
    return nonce + ct


def decrypt(key: bytes, data: bytes) -> bytes:
    """
    Decrypt AES-256-GCM. Raises InvalidTag if data was tampered with.
    """
    nonce, ct = data[:12], data[12:]
    return AESGCM(key).decrypt(nonce, ct, None)


# ── Helper ────────────────────────────────────────────────────────────────────

def center_window(window):
    window.update_idletasks()
    w, h = window.winfo_width(), window.winfo_height()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# ── Networking ────────────────────────────────────────────────────────────────

class PeerDiscovery:
    """UDP broadcast discovery"""

    def __init__(self, nickname: str, pub_bytes: bytes, on_peer_found, on_peer_lost):
        self.nickname      = nickname
        self.pub_bytes     = pub_bytes
        self.on_peer_found = on_peer_found
        self.on_peer_lost  = on_peer_lost
        self.peers         = {}
        self._stop         = threading.Event()
        self.local_ip      = self._get_local_ip()
        self._socks        = []

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        finally:
            s.close()

    def start(self):
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop,    daemon=True).start()
        threading.Thread(target=self._prune_loop,     daemon=True).start()

    def _broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socks.append(sock)
        payload = json.dumps({
            "type":     "announce",
            "nickname": self.nickname,
            "port":     CHAT_PORT
            # Note: we do NOT broadcast public keys here — they're exchanged
            # fresh per-session over TCP for perfect forward secrecy
        }).encode()
        while not self._stop.is_set():
            try:
                sock.sendto(payload, ("<broadcast>", DISCOVERY_PORT))
            except Exception:
                pass
            self._stop.wait(BROADCAST_INTERVAL)

    def _listen_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", DISCOVERY_PORT))
        sock.settimeout(1.0)
        self._socks.append(sock)
        while not self._stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                msg        = json.loads(data.decode())
                peer_ip    = addr[0]
                if peer_ip == self.local_ip:
                    continue
                if msg.get("type") == "announce":
                    is_new = peer_ip not in self.peers
                    self.peers[peer_ip] = {
                        "nickname":  msg["nickname"],
                        "port":      msg.get("port", CHAT_PORT),
                        "last_seen": time.time()
                    }
                    if is_new:
                        self.on_peer_found(peer_ip, msg["nickname"])
            except (socket.timeout, json.JSONDecodeError):
                pass

    def _prune_loop(self):
        while not self._stop.is_set():
            now  = time.time()
            dead = [ip for ip, d in self.peers.items()
                    if now - d["last_seen"] > 10]
            for ip in dead:
                del self.peers[ip]
                self.on_peer_lost(ip)
            self._stop.wait(5)

    def stop(self):
        self._stop.set()
        for s in self._socks:
            try: s.close()
            except: pass


class ChatServer:
    """Accepts incoming TCP connections"""

    def __init__(self, on_incoming):
        self.on_incoming = on_incoming
        self._stop       = threading.Event()
        self._sock       = None

    def start(self):
        threading.Thread(target=self._serve, daemon=True).start()

    def _serve(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("", CHAT_PORT))
        self._sock.listen(5)
        self._sock.settimeout(1.0)
        while not self._stop.is_set():
            try:
                conn, addr = self._sock.accept()
                threading.Thread(
                    target=self.on_incoming,
                    args=(conn, addr[0]),
                    daemon=True
                ).start()
            except socket.timeout:
                pass

    def stop(self):
        self._stop.set()
        if self._sock:
            try: self._sock.close()
            except: pass


class EncryptedSession:
    """
    Every payload is AES-256-GCM encrypted after an X25519 handshake.

    HANDSHAKE SEQUENCE:
      Initiator sends:  MAGIC + their_public_key (32 bytes)
      Responder sends:  MAGIC + their_public_key (32 bytes)
      Both derive the same session key via ECDH + HKDF
      All subsequent frames are: len(4) + encrypt(key, payload)

    MESSAGE TYPES:
      Text:  JSON {"type":"text", "text":"...", "nick":"..."}
      File:  4-byte header_len + JSON header + raw bytes  (all encrypted)
      Bye:   JSON {"type":"bye"}
    """
    MAGIC = b"CYBERAPP_V3"

    def __init__(self, sock: socket.socket, is_initiator: bool):
        self.sock  = sock
        self.key   = None
        self._lock = threading.Lock()

        priv, my_pub = generate_keypair()

        if is_initiator:
            self._send_raw(self.MAGIC + my_pub)
            their_data = self._recv_raw()
        else:
            their_data = self._recv_raw()
            self._send_raw(self.MAGIC + my_pub)

        assert their_data[:len(self.MAGIC)] == self.MAGIC, "Handshake failed: bad magic"
        their_pub = their_data[len(self.MAGIC):]
        self.key  = derive_session_key(priv, their_pub)

    # ── Public interface ──

    def send_text(self, payload: dict):
        data = json.dumps(payload).encode()
        enc  = encrypt(self.key, data)
        with self._lock:
            self._send_raw(enc)

    def send_file(self, msg_type: str, raw: bytes, filename: str):
        """
        Binary frame: [ 4-byte header_len ][ JSON header ][ raw bytes ]
        Then the whole thing is AES-encrypted before sending.
        """
        header     = json.dumps({"type": msg_type, "filename": filename,
                                  "size": len(raw)}).encode()
        header_len = struct.pack(">I", len(header))
        combined   = header_len + header + raw
        enc        = encrypt(self.key, combined)
        with self._lock:
            self._send_raw(enc)

    def recv(self):
        """
        Returns (msg_type, meta_dict, raw_bytes_or_None)
        Decrypts and parses the frame. Raises on connection error or tamper.
        """
        enc  = self._recv_raw()
        data = decrypt(self.key, enc)   # raises InvalidTag if tampered

        # Detect binary frame: check if first 4 bytes look like a small header length
        try:
            hlen = struct.unpack(">I", data[:4])[0]
            if 0 < hlen < 4096 and 4 + hlen <= len(data):
                header = json.loads(data[4:4 + hlen].decode())
                raw    = data[4 + hlen:]
                return header.get("type"), header, raw
        except Exception:
            pass

        msg = json.loads(data.decode())
        return msg.get("type"), msg, None

    def close(self):
        try: self.sock.close()
        except: pass

    # ── Internal framing ──

    def _send_raw(self, data: bytes):
        self.sock.sendall(struct.pack(">I", len(data)) + data)

    def _recv_raw(self) -> bytes:
        length = struct.unpack(">I", self._recvn(4))[0]
        return self._recvn(length)

    def _recvn(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionResetError("Peer disconnected")
            buf += chunk
        return buf


# ── GUI ───────────────────────────────────────────────────────────────────────

class MessagingWindow:
    def __init__(self, parent, session: EncryptedSession,
                 peer_nickname: str, my_nickname: str):
        self.parent        = parent
        self.session       = session
        self.peer_nickname = peer_nickname
        self.my_nickname   = my_nickname
        self._closed       = False
        self._photos       = []   # keep image references to prevent GC

        self.win = tk.Toplevel(parent)
        self.win.title(f"🔒 Chat with {peer_nickname}")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("700x560")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.win,
                 text=f"🔒  Encrypted Session  ▸  {peer_nickname}",
                 font=FONT_BIG, bg=DARK_BG, fg=ACCENT).pack(pady=(14, 2))
        tk.Label(self.win,
                 text="AES-256-GCM  •  X25519 ECDH  •  HKDF-SHA256  •  ephemeral keys",
                 font=FONT_SM, bg=DARK_BG, fg="#3A8899").pack()
        tk.Frame(self.win, height=1, bg=TEAL).pack(fill="x", pady=8, padx=20)

        self.msg_area = scrolledtext.ScrolledText(
            self.win, font=FONT_MAIN, bg=DARK_MID, fg=TEXT_FG,
            insertbackground=ACCENT, relief="flat",
            state="disabled", wrap="word", padx=10, pady=10
        )
        self.msg_area.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        self.msg_area.tag_config("me",   foreground=ACCENT)
        self.msg_area.tag_config("peer", foreground="#7DFFB0")
        self.msg_area.tag_config("sys",  foreground="#888888",
                                          font=("Consolas", 10, "italic"))
        self.msg_area.tag_config("err",  foreground="#FF6B6B")

        input_frame = tk.Frame(self.win, bg=DARK_BG)
        input_frame.pack(fill="x", padx=20, pady=(0, 14))

        self.entry = tk.Entry(input_frame, font=FONT_MAIN,
                              bg=DARK_MID, fg=TEXT_FG,
                              insertbackground=ACCENT, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._send_text())

        tk.Button(input_frame, text="Send", font=FONT_MAIN,
                  bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
                  command=self._send_text).pack(side="left", ipady=8, ipadx=12)

        tk.Button(input_frame, text="📎", font=("Consolas", 16),
                  bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
                  command=self._send_file).pack(side="left", ipady=4, ipadx=8,
                                                padx=(6, 0))

        center_window(self.win)
        self._append("sys",
            f"Session established with {peer_nickname}.\n"
            f"All messages and files are end-to-end encrypted.\n"
            f"Received files saved to: {STORAGE_DIR}\n")

        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _append(self, tag, text):
        def _do():
            ts = datetime.now().strftime("%H:%M")
            self.msg_area.configure(state="normal")
            self.msg_area.insert("end", f"[{ts}] {text}\n", tag)
            self.msg_area.configure(state="disabled")
            self.msg_area.see("end")
        if self.win.winfo_exists():
            self.win.after(0, _do)

    def _send_text(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        try:
            self.session.send_text({"type": "text", "text": text, "nick": self.my_nickname})
            self._append("me", f"You: {text}")
        except Exception as e:
            self._append("err", f"Send error: {e}")

    def _send_file(self):
        path = filedialog.askopenfilename(title="Select file to send")
        if not path:
            return
        path = Path(path)
        raw  = path.read_bytes()
        ext  = path.suffix.lower()
        ftype = "image" if ext in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp") \
                else "file"
        try:
            self.session.send_file(ftype, raw, path.name)
            self._append("me", f"You sent {ftype}: {path.name} ({len(raw):,} bytes)")
        except Exception as e:
            self._append("err", f"File send error: {e}")

    def _recv_loop(self):
        while not self._closed:
            try:
                msg_type, meta, raw = self.session.recv()

                if msg_type == "text":
                    nick = meta.get("nick", self.peer_nickname)
                    self._append("peer", f"{nick}: {meta.get('text', '')}")

                elif msg_type in ("image", "file"):
                    filename  = meta.get("filename", f"recv_{int(time.time())}")
                    save_path = STORAGE_DIR / filename
                    # Auto-deduplicate filenames
                    stem, suffix = Path(filename).stem, Path(filename).suffix
                    counter = 1
                    while save_path.exists():
                        save_path = STORAGE_DIR / f"{stem}_{counter}{suffix}"
                        counter  += 1
                    save_path.write_bytes(raw)
                    self._append("peer",
                        f"{self.peer_nickname} sent {msg_type}: "
                        f"{filename} ({len(raw):,} bytes)  →  {save_path}")
                    if msg_type == "image":
                        self._show_preview(save_path)

                elif msg_type == "bye":
                    self._append("sys", f"{self.peer_nickname} ended the session.")
                    break

            except ConnectionResetError:
                self._append("sys", "Connection closed by peer.")
                break
            except Exception as e:
                if not self._closed:
                    self._append("err", f"Receive error: {e}")
                break

    def _show_preview(self, path: Path):
        """Render a received image inline in the chat area."""
        def _do():
            try:
                img   = Image.open(path)
                img.thumbnail((280, 280))
                photo = ImageTk.PhotoImage(img)
                self.msg_area.configure(state="normal")
                self.msg_area.image_create("end", image=photo)
                self.msg_area.insert("end", "\n")
                self.msg_area.configure(state="disabled")
                self.msg_area.see("end")
                self._photos.append(photo)  # prevent garbage collection
            except Exception:
                pass
        if self.win.winfo_exists():
            self.win.after(0, _do)

    def _on_close(self):
        self._closed = True
        try:
            self.session.send_text({"type": "bye"})
        except Exception:
            pass
        self.session.close()
        self.win.destroy()


class ChatWindow:
    def __init__(self, parent, nickname):
        self.parent   = parent
        self.nickname = nickname
        self.sessions = {}

        self.win = tk.Toplevel(parent)
        self.win.title("CyberApp — Lobby")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("1000x700")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.win, text="CYBERAPP",
                 font=("Consolas", 28, "bold"), bg=DARK_BG, fg=ACCENT).pack(pady=(20, 0))
        tk.Label(self.win, text=f"Logged in as  ›  {nickname}",
                 font=FONT_SM, bg=DARK_BG, fg=TEAL).pack()
        tk.Frame(self.win, height=1, bg=TEAL).pack(fill="x", padx=30, pady=12)

        cols = tk.Frame(self.win, bg=DARK_BG)
        cols.pack(fill="both", expand=True, padx=30)

        left = tk.Frame(cols, bg=DARK_MID)
        left.pack(side="left", fill="y", padx=(0, 12), ipadx=10, ipady=10)

        tk.Label(left, text="PEERS ONLINE",
                 font=("Consolas", 11, "bold"), bg=DARK_MID, fg=TEAL).pack(pady=(10, 4))

        self.peer_listbox = tk.Listbox(
            left, font=FONT_MAIN, bg=DARK_MID, fg=ACCENT,
            selectbackground=TEAL, selectforeground=TEXT_FG,
            relief="flat", borderwidth=0, width=22, height=20, activestyle="none"
        )
        self.peer_listbox.pack(padx=8, pady=4, fill="y", expand=True)
        self.peer_listbox.bind("<<ListboxSelect>>", self._on_peer_select)
        self.peer_listbox.bind("<Double-Button-1>",  self._on_peer_double_click)

        tk.Button(left, text="⟳  Refresh", font=FONT_SM,
                  bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
                  command=self._manual_refresh).pack(pady=8, padx=8, fill="x")

        right = tk.Frame(cols, bg=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        self.info_label = tk.Label(right,
            text="Scanning for peers on your network...\n\n"
                 "Double-click a peer to open an\nencrypted session.",
            font=("Consolas", 14), bg=DARK_BG, fg="#3A8899", justify="left")
        self.info_label.pack(anchor="nw", pady=20)

        self.connect_btn = tk.Button(right, text="🔒  Start Encrypted Chat",
            font=FONT_MAIN, bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
            state="disabled", command=self._start_chat_with_selected)
        self.connect_btn.pack(anchor="nw", pady=8, ipadx=12, ipady=8)

        self.status_var = tk.StringVar(value="Scanning network...")
        tk.Label(self.win, textvariable=self.status_var,
                 font=FONT_SM, bg=DARK_BG, fg="#3A8899",
                 anchor="w").pack(side="bottom", fill="x", padx=30, pady=8)

        center_window(self.win)
        self.win.focus_force()

        self._peer_map = {}

        # Generate long-term identity keypair (used only for display, not crypto)
        _, self._pub_bytes = generate_keypair()

        self._discovery = PeerDiscovery(
            nickname=nickname,
            pub_bytes=self._pub_bytes,
            on_peer_found=self._on_peer_found,
            on_peer_lost=self._on_peer_lost
        )
        self._discovery.start()

        self._server = ChatServer(on_incoming=self._on_incoming_connection)
        self._server.start()

    def _on_peer_found(self, ip, peer_nickname):
        self._peer_map[ip] = self._discovery.peers.get(ip, {"nickname": peer_nickname})
        self.win.after(0, self._rebuild_listbox)
        self.win.after(0, lambda: self.status_var.set(f"New peer: {peer_nickname} ({ip})"))

    def _on_peer_lost(self, ip):
        self._peer_map.pop(ip, None)
        self.win.after(0, self._rebuild_listbox)

    def _rebuild_listbox(self):
        self.peer_listbox.delete(0, "end")
        for ip, info in self._peer_map.items():
            self.peer_listbox.insert("end", f"{info['nickname']}  ({ip})")

    def _manual_refresh(self):
        self._peer_map = dict(self._discovery.peers)
        self._rebuild_listbox()
        self.status_var.set(f"{len(self._peer_map)} peer(s) visible.")

    def _selected_peer_ip(self):
        sel = self.peer_listbox.curselection()
        if not sel:
            return None
        return self.peer_listbox.get(sel[0]).split("(")[-1].rstrip(")").strip()

    def _on_peer_select(self, event):
        ip = self._selected_peer_ip()
        if ip and ip in self._peer_map:
            info = self._peer_map[ip]
            self.info_label.config(
                text=f"Peer:  {info['nickname']}\nIP:    {ip}"
                     f"\n\nDouble-click to open encrypted session.")
            self.connect_btn.config(state="normal")

    def _on_peer_double_click(self, event):
        self._start_chat_with_selected()

    def _start_chat_with_selected(self):
        ip = self._selected_peer_ip()
        if not ip or ip not in self._peer_map:
            return
        if ip in self.sessions:
            try: self.sessions[ip].win.lift()
            except: pass
            return
        info = self._peer_map[ip]
        threading.Thread(
            target=self._connect_thread,
            args=(ip, info.get("port", CHAT_PORT), info["nickname"]),
            daemon=True
        ).start()

    def _connect_thread(self, ip, port, peer_nickname):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(8)
            sock.connect((ip, port))
            sock.settimeout(None)
            session = EncryptedSession(sock, is_initiator=True)
            self.win.after(0, lambda: self._open_messaging(session, ip, peer_nickname))
        except Exception as e:
            self.win.after(0, lambda: messagebox.showerror(
                "Connection Failed", f"Could not connect to {peer_nickname}:\n{e}"))

    def _on_incoming_connection(self, conn: socket.socket, peer_ip: str):
        try:
            session       = EncryptedSession(conn, is_initiator=False)
            peer_info     = self._peer_map.get(peer_ip, {})
            peer_nickname = peer_info.get("nickname", peer_ip)
            self.win.after(0, lambda: self._open_messaging(session, peer_ip, peer_nickname))
        except Exception as e:
            print(f"[Server] Handshake failed from {peer_ip}: {e}")

    def _open_messaging(self, session, peer_ip, peer_nickname):
        if peer_ip in self.sessions:
            try: self.sessions[peer_ip].win.lift()
            except: pass
            return
        mw = MessagingWindow(self.win, session, peer_nickname, self.nickname)
        self.sessions[peer_ip] = mw

    def _on_close(self):
        self._discovery.stop()
        self._server.stop()
        for mw in list(self.sessions.values()):
            try: mw._on_close()
            except: pass
        self.parent.deiconify()
        self.win.destroy()


class CyberApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CyberApp")
        self.root.configure(bg=DARK_BG)
        self.root.geometry("800x600")

        tk.Label(self.root, text="CYBERAPP",
                 font=("Consolas", 36, "bold"), bg=DARK_BG, fg=ACCENT).pack(pady=(60, 4))
        tk.Label(self.root,
                 text="end-to-end encrypted  •  peer-to-peer  •  ephemeral",
                 font=FONT_SM, bg=DARK_BG, fg=TEAL).pack()
        tk.Button(self.root, text="Start Chatting  →",
                  font=("Consolas", 18), bg=TEAL, fg=ACCENT,
                  relief="flat", cursor="hand2",
                  command=self._on_start).pack(pady=40, ipadx=20, ipady=10)

        if os.path.exists("cyberlogo.png"):
            try:
                logo  = Image.open("cyberlogo.png").resize((220, 220))
                photo = ImageTk.PhotoImage(logo)
                lbl   = tk.Label(self.root, image=photo, bg=DARK_BG)
                lbl.image = photo
                lbl.pack()
            except Exception:
                pass

        center_window(self.root)

    def _on_start(self):
        self.root.withdraw()
        SignupWindow(self.root)

    def run(self):
        self.root.mainloop()


class SignupWindow:
    def __init__(self, parent):
        self.parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title("Profile Setup")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("420x320")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.win, text="Choose Your Nickname",
                 font=FONT_BIG, bg=DARK_BG, fg=ACCENT).pack(pady=(40, 6))
        tk.Label(self.win,
                 text="This is how others will see you on the network.",
                 font=FONT_SM, bg=DARK_BG, fg=TEAL).pack()

        self.entry = tk.Entry(self.win, font=("Consolas", 18),
                              bg=DARK_MID, fg=TEXT_FG,
                              insertbackground=ACCENT, relief="flat", justify="center")
        self.entry.pack(pady=20, ipadx=10, ipady=8, padx=40, fill="x")
        self.entry.bind("<Return>", lambda e: self._submit())

        tk.Button(self.win, text="Enter  →", font=("Consolas", 16),
                  bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
                  command=self._submit).pack(pady=10, ipadx=16, ipady=8)

        center_window(self.win)
        self.entry.focus_set()

    def _submit(self):
        nickname = self.entry.get().strip()
        if not nickname:
            messagebox.showerror("Error", "Please enter a nickname.")
            return
        self.win.destroy()
        ChatWindow(self.parent, nickname)

    def _on_close(self):
        self.parent.deiconify()
        self.win.destroy()


if __name__ == "__main__":
    CyberApp().run()