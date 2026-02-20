import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import os

# ── Design Constants ──────────────────────────────────────────────────────────
DARK_BG   = "#05053B"   # deep navy — main background
DARK_MID  = "#0D0D5A"   # slightly lighter navy — input/panel backgrounds
ACCENT    = "#22B9FF"   # electric blue — primary text/highlights
TEAL      = "#2D5961"   # muted teal — buttons and secondary UI
TEXT_FG   = "#E0F7FF"   # near-white — body text

FONT_MAIN = ("Consolas", 13)
FONT_BIG  = ("Consolas", 20, "bold")
FONT_SM   = ("Consolas", 11)

# Mock peers 
MOCK_PEERS = [
    {"nickname": "Steve", "ip": "192.168.1.10"},
    {"nickname": "xXjohn_toeXx", "ip": "192.168.1.11"},
    {"nickname": "papa_smurf", "ip": "192.168.1.12"},
]



def center_window(window):
    """Centers any Tk window on the screen."""
    window.update_idletasks()
    w  = window.winfo_width()
    h  = window.winfo_height()
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    window.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


# ── Screen 1: Startup ─────────────────────────────────────────────────────────

class CyberApp:
    """
    The root Tk window. Acts as the application entry point.
    All subsequent windows are Toplevel children of this root.
    """
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CyberApp")
        self.root.configure(bg=DARK_BG)
        self.root.geometry("800x600")

        # App title
        tk.Label(self.root,
                 text="CYBERAPP",
                 font=("Consolas", 36, "bold"),
                 bg=DARK_BG, fg=ACCENT).pack(pady=(60, 4))


        # Start button — triggers the signup window
        tk.Button(self.root,
                  text="Start Chatting  →",
                  font=("Consolas", 18),
                  bg=TEAL, fg=ACCENT,
                  activebackground=ACCENT, activeforeground=DARK_BG,
                  relief="flat", cursor="hand2",
                  command=self._on_start).pack(pady=40, ipadx=20, ipady=10)

        # Optional logo (gracefully skipped if file not found)
        if os.path.exists("cyberlogo.png"):
            try:
                logo  = Image.open("cyberlogo.png").resize((220, 220))
                photo = ImageTk.PhotoImage(logo)
                lbl   = tk.Label(self.root, image=photo, bg=DARK_BG)
                lbl.image = photo   # <-- keep reference to prevent garbage collection
                lbl.pack()
            except Exception:
                pass

        center_window(self.root)

    def _on_start(self):
        """Hide the startup window and open the signup window."""
        self.root.withdraw()
        SignupWindow(self.root)

    def run(self):
        self.root.mainloop()


# ── Screen 2: Profile Setup ───────────────────────────────────────────────────

class SignupWindow:
    """
    A Toplevel window (child of root) that collects the user's nickname.
    Toplevel windows share the same event loop as the root window.
    """
    def __init__(self, parent):
        self.parent = parent

        self.win = tk.Toplevel(parent)
        self.win.title("Profile Setup")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("420x320")

        # If user closes this window, bring the root back
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        tk.Label(self.win,
                 text="Choose Your Nickname",
                 font=FONT_BIG, bg=DARK_BG, fg=ACCENT).pack(pady=(40, 6))

        tk.Label(self.win,
                 text="This is how others will see you on the network.",
                 font=FONT_SM, bg=DARK_BG, fg=TEAL).pack()

        # Entry widget — text input box
        self.entry = tk.Entry(self.win,
                              font=("Consolas", 18),
                              bg=DARK_MID, fg=TEXT_FG,
                              insertbackground=ACCENT,
                              relief="flat", justify="center")
        self.entry.pack(pady=20, ipadx=10, ipady=8, padx=40, fill="x")

        # Bind the Enter key as an alternative to clicking Submit
        self.entry.bind("<Return>", lambda e: self._submit())

        tk.Button(self.win,
                  text="Enter  →",
                  font=("Consolas", 16),
                  bg=TEAL, fg=ACCENT,
                  relief="flat", cursor="hand2",
                  command=self._submit).pack(pady=10, ipadx=16, ipady=8)

        center_window(self.win)
        self.entry.focus_set()  # auto-focus the entry field

    def _submit(self):
        nickname = self.entry.get().strip()
        if not nickname:
            messagebox.showerror("Error", "Please enter a nickname.")
            return
        self.win.destroy()
        ChatWindow(self.parent, nickname)

    def _on_close(self):
        """User closed signup — restore the main window."""
        self.parent.deiconify()
        self.win.destroy()


# ── Screen 3: Lobby ───────────────────────────────────────────────────────────

class ChatWindow:
    """
    Main lobby. Shows online peers and lets you open a chat session.
    """
    def __init__(self, parent, nickname):
        self.parent   = parent
        self.nickname = nickname

        self.win = tk.Toplevel(parent)
        self.win.title("CyberApp — Lobby")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("1000x700")
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Header ──
        tk.Label(self.win,
                 text="CYBERAPP",
                 font=("Consolas", 28, "bold"),
                 bg=DARK_BG, fg=ACCENT).pack(pady=(20, 0))

        tk.Label(self.win,
                 text=f"Logged in as  ›  {nickname}",
                 font=FONT_SM, bg=DARK_BG, fg=TEAL).pack()

        tk.Frame(self.win, height=1, bg=TEAL).pack(fill="x", padx=30, pady=12)

        # ── Two-column layout ──
        cols = tk.Frame(self.win, bg=DARK_BG)
        cols.pack(fill="both", expand=True, padx=30)

        # Left panel — peer list
        left = tk.Frame(cols, bg=DARK_MID)
        left.pack(side="left", fill="y", padx=(0, 12), ipadx=10, ipady=10)

        tk.Label(left,
                 text="PEERS ONLINE",
                 font=("Consolas", 11, "bold"),
                 bg=DARK_MID, fg=TEAL).pack(pady=(10, 4))

        # Listbox — a scrollable list of selectable items
        self.peer_listbox = tk.Listbox(
            left,
            font=FONT_MAIN,
            bg=DARK_MID, fg=ACCENT,
            selectbackground=TEAL, selectforeground=TEXT_FG,
            relief="flat", borderwidth=0,
            width=22, height=20,
            activestyle="none"
        )
        self.peer_listbox.pack(padx=8, pady=4, fill="y", expand=True)

        # Populate with mocked peers
        for peer in MOCK_PEERS:
            self.peer_listbox.insert(tk.END, f"{peer['nickname']}  ({peer['ip']})")

        # Bind selection event
        self.peer_listbox.bind("<<ListboxSelect>>", self._on_peer_select)
        # Double-click to open chat
        self.peer_listbox.bind("<Double-Button-1>",  self._on_peer_double_click)

        tk.Button(left,
                  text="⟳  Refresh",
                  font=FONT_SM,
                  bg=TEAL, fg=ACCENT,
                  relief="flat", cursor="hand2",
                  command=self._refresh).pack(pady=8, padx=8, fill="x")

        # Right panel — info + connect button
        right = tk.Frame(cols, bg=DARK_BG)
        right.pack(side="left", fill="both", expand=True)

        self.info_label = tk.Label(
            right,
            text="Select a peer from the list\nto start a chat session.",
            font=("Consolas", 14),
            bg=DARK_BG, fg="#3A8899",
            justify="left"
        )
        self.info_label.pack(anchor="nw", pady=20)

        self.connect_btn = tk.Button(
            right,
            text="🔒  Start Encrypted Chat",
            font=FONT_MAIN,
            bg=TEAL, fg=ACCENT,
            relief="flat", cursor="hand2",
            state="disabled",       # disabled until a peer is selected
            command=self._start_chat_with_selected
        )
        self.connect_btn.pack(anchor="nw", pady=8, ipadx=12, ipady=8)

        # Status bar along the bottom
        self.status_var = tk.StringVar(value="[Peers are mocked.]")
        tk.Label(self.win,
                 textvariable=self.status_var,
                 font=FONT_SM, bg=DARK_BG, fg="#3A8899",
                 anchor="w").pack(side="bottom", fill="x", padx=30, pady=8)

        center_window(self.win)
        self.win.focus_force()

        self._selected_peer = None

    def _on_peer_select(self, event):
        sel = self.peer_listbox.curselection()
        if not sel:
            return
        idx  = sel[0]
        peer = MOCK_PEERS[idx]
        self._selected_peer = peer
        self.info_label.config(
            text=f"Peer:  {peer['nickname']}\nIP:    {peer['ip']}\n\n"
                 f"Double-click or press button\nto open encrypted session."
        )
        self.connect_btn.config(state="normal")

    def _on_peer_double_click(self, event):
        self._start_chat_with_selected()

    def _start_chat_with_selected(self):
        if not self._selected_peer:
            return
        MessagingWindow(self.win,
                        peer_nickname=self._selected_peer["nickname"],
                        my_nickname=self.nickname,
                        session=None)   # fake session for now

    def _refresh(self):
        self.status_var.set("Refreshed. (Live discovery to be added)")

    def _on_close(self):
        self.parent.deiconify()
        self.win.destroy()


# ── Screen 4: Messaging Window ────────────────────────────────────────────────

class MessagingWindow:
    """
    The actual chat UI. Messages are local only (no sending/receiving).
    """
    def __init__(self, parent, peer_nickname, my_nickname, session):
        self.parent = parent
        self.peer_nickname = peer_nickname
        self.my_nickname = my_nickname
        self.session = session

        self.win = tk.Toplevel(parent)
        self.win.title(f"🔒 Chat with {peer_nickname}")
        self.win.configure(bg=DARK_BG)
        self.win.geometry("700x550")

        # Title
        tk.Label(self.win,
                 text=f"🔒  Chat  ▸  {peer_nickname}",
                 font=FONT_BIG, bg=DARK_BG, fg=ACCENT).pack(pady=(14, 2))

        tk.Label(self.win,
                 text="Encryption to be added]",
                 font=FONT_SM, bg=DARK_BG, fg="#3A8899").pack()

        tk.Frame(self.win, height=1, bg=TEAL).pack(fill="x", pady=8, padx=20)

        # ── Message display area ──
        # ScrolledText = Text widget + scrollbar, good for chat logs
        self.msg_area = scrolledtext.ScrolledText(
            self.win,
            font=FONT_MAIN,
            bg=DARK_MID, fg=TEXT_FG,
            insertbackground=ACCENT,
            relief="flat", state="disabled",
            wrap="word", padx=10, pady=10
        )
        self.msg_area.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # Named tags for color-coding messages by sender
        self.msg_area.tag_config("me",   foreground=ACCENT)
        self.msg_area.tag_config("peer", foreground="#7DFFB0")
        self.msg_area.tag_config("sys",  foreground="#888888",
                                          font=("Consolas", 10, "italic"))

        # ── Input row ──
        input_frame = tk.Frame(self.win, bg=DARK_BG)
        input_frame.pack(fill="x", padx=20, pady=(0, 14))

        self.entry = tk.Entry(
            input_frame,
            font=FONT_MAIN,
            bg=DARK_MID, fg=TEXT_FG,
            insertbackground=ACCENT,
            relief="flat"
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self._send_text())

        tk.Button(input_frame,
                  text="Send",
                  font=FONT_MAIN,
                  bg=TEAL, fg=ACCENT,
                  relief="flat", cursor="hand2",
                  command=self._send_text).pack(side="left", ipady=8, ipadx=12)

        center_window(self.win)
        self._append("sys", f"Session opened with {peer_nickname}")

    def _append(self, tag, text):
        """Thread-safe way to add a line to the message area."""
        self.msg_area.configure(state="normal")
        self.msg_area.insert("end", f"{text}\n", tag)
        self.msg_area.configure(state="disabled")
        self.msg_area.see("end")   # auto-scroll to bottom

    def _send_text(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append("me", f"You: {text}")
        #no real send
        self._append("sys", "(message not sent)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    CyberApp().run()