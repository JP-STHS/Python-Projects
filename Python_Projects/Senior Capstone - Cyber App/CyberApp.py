import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from PIL import Image, ImageTk
import os, socket, threading, json, time, struct
from datetime import datetime

# ── Design Constants ──────────────────────────────────────────────────────────
DARK_BG   = "#05053B"   # deep navy — main background
DARK_MID  = "#0D0D5A"   # slightly lighter navy — input/panel backgrounds
ACCENT    = "#22B9FF"   # electric blue — primary text/highlights
TEAL      = "#2D5961"   # muted teal — buttons and secondary UI
TEXT_FG   = "#E0F7FF"   # near-white — body text

FONT_MAIN = ("Consolas", 13)
FONT_BIG  = ("Consolas", 20, "bold")
FONT_SM   = ("Consolas", 11)

DISCOVERY_PORT   = 55555   # UDP — broadcast on this port to announce presence
CHAT_PORT        = 55556   # TCP — listen here for incoming chat connections
BROADCAST_INTERVAL = 3     # seconds between each UDP announcement


# ── Helper ────────────────────────────────────────────────────────────────────

def center_window(window):
    window.update_idletasks()
    w, h = window.winfo_width(), window.winfo_height()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


# ── Networking ────────────────────────────────────────────────────────────────

class PeerDiscovery:
    """
    Announces this device on the LAN using UDP broadcast, and listens for
    announcements from other instances.

    UDP broadcast works by sending a packet to the special address
    "<broadcast>" on your subnet — every device on the LAN receives it
    without the sender needing to know anyone's IP address.

    self._stop is a threading.Event. Calling .set() tells all threads
    to exit their loops cleanly, avoiding zombie threads.
    """

    def __init__(self, nickname: str, on_peer_found, on_peer_lost):
        self.nickname      = nickname
        self.on_peer_found = on_peer_found   # callback(ip, nickname)
        self.on_peer_lost  = on_peer_lost    # callback(ip)
        self.peers         = {}              # ip -> {nickname, last_seen}
        self._stop         = threading.Event()
        self.local_ip      = self._get_local_ip()
        self._socks        = []  # track sockets so we can close them on stop

    def _get_local_ip(self) -> str:
        """Trick to find our outbound IP without actually sending anything."""
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
        """Send a JSON announcement packet every BROADCAST_INTERVAL seconds."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socks.append(sock)

        payload = json.dumps({
            "type":     "announce",
            "nickname": self.nickname,
            "port":     CHAT_PORT
        }).encode()

        while not self._stop.is_set():
            try:
                sock.sendto(payload, ("<broadcast>", DISCOVERY_PORT))
            except Exception:
                pass
            # Use Event.wait() instead of time.sleep() so we can wake up early on stop
            self._stop.wait(BROADCAST_INTERVAL)

    def _listen_loop(self):
        """Listen for announcements from other peers."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", DISCOVERY_PORT))
        sock.settimeout(1.0)   # timeout so we check _stop regularly
        self._socks.append(sock)

        while not self._stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                msg        = json.loads(data.decode())
                peer_ip    = addr[0]

                # Ignore our own broadcasts
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

            except socket.timeout:
                pass
            except json.JSONDecodeError:
                pass

    def _prune_loop(self):
        """Remove peers that haven't broadcast in 10 seconds."""
        while not self._stop.is_set():
            now  = time.time()
            dead = [ip for ip, d in self.peers.items()
                    if now - d["last_seen"] > 10]
            for ip in dead:
                del self.peers[ip]
                self.on_peer_lost(ip)
            self._stop.wait(5)

    def stop(self):
        """Signal all threads to exit, then close all sockets."""
        self._stop.set()
        for s in self._socks:
            try:
                s.close()
            except Exception:
                pass


class ChatServer:
    """
    Listens for incoming TCP connections on CHAT_PORT.
    Each accepted connection is handed off to a callback on its own thread.
    """

    def __init__(self, on_incoming):
        self.on_incoming = on_incoming   # callback(socket, peer_ip)
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
            try:
                self._sock.close()
            except Exception:
                pass


class PlaintextSession:
    """
    Wraps a TCP socket with a simple length-prefixed JSON protocol.

    Wire format:
        [ 4-byte big-endian length ][ JSON bytes ]

    The length prefix lets the receiver know exactly how many bytes to read,
    solving the "TCP is a stream, not packets" problem.

    In Week 3 this class is replaced by EncryptedSession which adds
    X25519 + AES-256-GCM on top of the same wire format.
    """

    def __init__(self, sock: socket.socket):
        self.sock  = sock
        self._lock = threading.Lock()   # prevent concurrent writes corrupting the stream

    def send(self, payload: dict):
        data = json.dumps(payload).encode()
        # Pack length as 4 unsigned bytes, big-endian
        framed = struct.pack(">I", len(data)) + data
        with self._lock:
            self.sock.sendall(framed)

    def recv(self) -> dict:
        length_bytes = self._recvn(4)
        length       = struct.unpack(">I", length_bytes)[0]
        data         = self._recvn(length)
        return json.loads(data.decode())

    def _recvn(self, n: int) -> bytes:
        """Read exactly n bytes, blocking until available."""
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionResetError("Peer disconnected")
            buf += chunk
        return buf

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

# ── GUI ───────────────────────────────────────────────────────────────────────

def center_window(window):
    window.update_idletasks()
    w, h = window.winfo_width(), window.winfo_height()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


class MessagingWindow:
    def __init__(self, parent, session: PlaintextSession,
                 peer_nickname: str, my_nickname: str):
        self.parent        = parent
        self.session       = session
        self.peer_nickname = peer_nickname
        self.my_nickname   = my_nickname
        self._closed       = False

        self.win = tk.Toplevel(parent)
        self.win.title(f"Chat with {peer_nickname} [plaintext]")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("700x550")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.win,
                 text=f"Chat  ▸  {peer_nickname}",
                 font=FONT_BIG, bg=DARK_BG, fg=ACCENT).pack(pady=(14, 2))

        tk.Label(self.win,
                 text="[Week 2 — plaintext TCP  •  encryption arrives in Week 3]",
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

        center_window(self.win)
        self._append("sys", f"Connected to {peer_nickname}. "
                            f"Messages are plaintext in Week 2.\n")

        # Start background thread to receive incoming messages
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _append(self, tag, text):
        """
        GUI updates MUST happen on the main thread.
        widget.after(0, fn) schedules fn to run on the main thread
        at the next opportunity — this is the standard Tkinter pattern.
        """
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
            self.session.send({"type": "text", "text": text, "nick": self.my_nickname})
            self._append("me", f"You: {text}")
        except Exception as e:
            self._append("err", f"Send error: {e}")

    def _recv_loop(self):
        """Runs on a background thread — receives messages and schedules GUI updates."""
        while not self._closed:
            try:
                msg = self.session.recv()
                if msg.get("type") == "text":
                    nick = msg.get("nick", self.peer_nickname)
                    self._append("peer", f"{nick}: {msg.get('text', '')}")
                elif msg.get("type") == "bye":
                    self._append("sys", f"{self.peer_nickname} ended the session.")
                    break
            except ConnectionResetError:
                self._append("sys", "Connection closed by peer.")
                break
            except Exception as e:
                if not self._closed:
                    self._append("err", f"Receive error: {e}")
                break

    def _on_close(self):
        self._closed = True
        try:
            self.session.send({"type": "bye"})
        except Exception:
            pass
        self.session.close()
        self.win.destroy()


class ChatWindow:
    def __init__(self, parent, nickname):
        self.parent   = parent
        self.nickname = nickname
        self.sessions = {}   # peer_ip -> MessagingWindow

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

        # Left — peer list
        left = tk.Frame(cols, bg=DARK_MID)
        left.pack(side="left", fill="y", padx=(0, 12), ipadx=10, ipady=10)

        tk.Label(left, text="PEERS ONLINE",
                 font=("Consolas", 11, "bold"), bg=DARK_MID, fg=TEAL).pack(pady=(10, 4))

        self.peer_listbox = tk.Listbox(
            left, font=FONT_MAIN,
            bg=DARK_MID, fg=ACCENT,
            selectbackground=TEAL, selectforeground=TEXT_FG,
            relief="flat", borderwidth=0,
            width=22, height=20, activestyle="none"
        )
        self.peer_listbox.pack(padx=8, pady=4, fill="y", expand=True)
        self.peer_listbox.bind("<<ListboxSelect>>", self._on_peer_select)
        self.peer_listbox.bind("<Double-Button-1>",  self._on_peer_double_click)

        tk.Button(left, text="⟳  Refresh", font=FONT_SM,
                  bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
                  command=self._manual_refresh).pack(pady=8, padx=8, fill="x")

        # Right — info + connect
        right = tk.Frame(cols, bg=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        self.info_label = tk.Label(
            right,
            text="Scanning for peers on your network...\n\nDouble-click a peer to chat.",
            font=("Consolas", 14), bg=DARK_BG, fg="#3A8899", justify="left"
        )
        self.info_label.pack(anchor="nw", pady=20)

        self.connect_btn = tk.Button(
            right, text="Connect", font=FONT_MAIN,
            bg=TEAL, fg=ACCENT, relief="flat", cursor="hand2",
            state="disabled", command=self._start_chat_with_selected
        )
        self.connect_btn.pack(anchor="nw", pady=8, ipadx=12, ipady=8)

        self.status_var = tk.StringVar(value="Scanning network...")
        tk.Label(self.win, textvariable=self.status_var,
                 font=FONT_SM, bg=DARK_BG, fg="#3A8899",
                 anchor="w").pack(side="bottom", fill="x", padx=30, pady=8)

        center_window(self.win)
        self.win.focus_force()

        # Internal peer map: ip -> {nickname, port}
        self._peer_map = {}

        # Start discovery
        self._discovery = PeerDiscovery(
            nickname=nickname,
            on_peer_found=self._on_peer_found,
            on_peer_lost=self._on_peer_lost
        )
        self._discovery.start()

        # Start incoming connection server
        self._server = ChatServer(on_incoming=self._on_incoming_connection)
        self._server.start()

    # ── Peer list management ──

    def _on_peer_found(self, ip, peer_nickname):
        """Called from discovery thread — must schedule GUI update on main thread."""
        self._peer_map[ip] = self._discovery.peers.get(ip, {"nickname": peer_nickname})
        self.win.after(0, self._rebuild_listbox)
        self.win.after(0, lambda: self.status_var.set(
            f"New peer: {peer_nickname} ({ip})"))

    def _on_peer_lost(self, ip):
        self._peer_map.pop(ip, None)
        self.win.after(0, self._rebuild_listbox)

    def _rebuild_listbox(self):
        self.peer_listbox.delete(0, "end")
        for ip, info in self._peer_map.items():
            self.peer_listbox.insert("end", f"{info['nickname']}  ({ip})")

    def _manual_refresh(self):
        # Sync our map from discovery's current state
        self._peer_map = dict(self._discovery.peers)
        self._rebuild_listbox()
        self.status_var.set(f"{len(self._peer_map)} peer(s) visible.")

    def _selected_peer_ip(self):
        sel = self.peer_listbox.curselection()
        if not sel:
            return None
        label = self.peer_listbox.get(sel[0])
        return label.split("(")[-1].rstrip(")").strip()

    def _on_peer_select(self, event):
        ip = self._selected_peer_ip()
        if ip and ip in self._peer_map:
            info = self._peer_map[ip]
            self.info_label.config(
                text=f"Peer:  {info['nickname']}\nIP:    {ip}"
                     f"\n\nDouble-click to connect.")
            self.connect_btn.config(state="normal")

    def _on_peer_double_click(self, event):
        self._start_chat_with_selected()

    # ── Outgoing connection ──

    def _start_chat_with_selected(self):
        ip = self._selected_peer_ip()
        if not ip or ip not in self._peer_map:
            return
        if ip in self.sessions:
            try:
                self.sessions[ip].win.lift()
            except Exception:
                pass
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
            session = PlaintextSession(sock)
            self.win.after(0, lambda: self._open_messaging(session, ip, peer_nickname))
        except Exception as e:
            self.win.after(0, lambda: messagebox.showerror(
                "Connection Failed", f"Could not connect to {peer_nickname}:\n{e}"))

    # ── Incoming connection ──

    def _on_incoming_connection(self, conn: socket.socket, peer_ip: str):
        session       = PlaintextSession(conn)
        peer_info     = self._peer_map.get(peer_ip, {})
        peer_nickname = peer_info.get("nickname", peer_ip)
        self.win.after(0, lambda: self._open_messaging(session, peer_ip, peer_nickname))

    # ── Open messaging window ──

    def _open_messaging(self, session, peer_ip, peer_nickname):
        if peer_ip in self.sessions:
            try:
                self.sessions[peer_ip].win.lift()
                return
            except Exception:
                pass
        mw = MessagingWindow(self.win, session, peer_nickname, self.nickname)
        self.sessions[peer_ip] = mw

    # ── Clean shutdown ──

    def _on_close(self):
        """
        Stop all background threads BEFORE destroying the window.
        This prevents the terminal from hanging after the GUI closes.
        """
        self._discovery.stop()
        self._server.stop()
        # Close any open sessions
        for mw in list(self.sessions.values()):
            try:
                mw._on_close()
            except Exception:
                pass
        self.parent.deiconify()
        self.win.destroy()

# ── Screen 1: Startup ─────────────────────────────────────────────────────────

class CyberApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CyberApp")
        self.root.configure(bg=DARK_BG)
        self.root.geometry("800x600")

        tk.Label(self.root, text="CYBERAPP",
                 font=("Consolas", 36, "bold"), bg=DARK_BG, fg=ACCENT).pack(pady=(60, 4))

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