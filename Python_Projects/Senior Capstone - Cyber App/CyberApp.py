#TODO: Main screen will have button to open new window - new window must have nickname config as well as texting functionality - 
#texting functionality comes first, must be encrypted
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os


def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")
class CyberApp:
    def __init__(self):
        #Initial main window
        self.startup_window = tk.Tk()
        self.startup_window.title("CyberApp")
        self.startup_window.configure(bg="#05053B")
        self.startup_window.geometry("800x600")

        self.label = tk.Label(self.startup_window, text="Encrypted Texting!", font=("Arial", 24),bg="#05053B",fg="#22B9FF")
        self.label.pack(pady=20)

        self.signupbutton = tk.Button(self.startup_window, text="Start Chatting", font=("Arial", 24), justify="left",command=self.on_button_click)
        self.signupbutton.pack(pady=20, anchor="w", padx=20)
        self.signupbutton.configure(bg="#2D5961",fg="#22B9FF")

        logo = ImageTk.PhotoImage(Image.open("cyberlogo.png").resize((300, 300)))
        self.img_label = tk.Label(self.startup_window, image=logo, bg="#05053B")
        self.img_label.image = logo
        self.img_label.pack(padx=100, anchor="e")

        center_window(self.startup_window)
    
    def on_button_click(self):
        self.startup_window.withdraw()
        SignupWindow(self.startup_window)
    def run(self):
        self.startup_window.mainloop()

class SignupWindow:
    def __init__(self, parent):
        self.parent = parent
        self.signup_window = tk.Toplevel(parent)
        self.signup_window.title("Profile Setup")
        self.signup_window.configure(bg="#05053B")
        self.signup_window.geometry("400x700")
        self.label = tk.Label(self.signup_window, text="Profile Setup", font=("Arial", 24),bg="#05053B",fg="#22B9FF")
        self.label.pack(pady=20)

        self.nickname_label = tk.Label(self.signup_window, text="Nickname:", font=("Arial", 18),bg="#05053B",fg="#22B9FF")
        self.nickname_label.pack(pady=10)
        self.nickname_entry = tk.Entry(self.signup_window, font=("Arial", 18))
        self.nickname_entry.pack(pady=10)

        self.submit_button = tk.Button(self.signup_window, text="Submit", font=("Arial", 18), command=self.submit_nickname)
        self.submit_button.pack(pady=20)
        center_window(self.signup_window)
    def submit_nickname(self):
        nickname = self.nickname_entry.get()
        if not nickname:
            tk.messagebox.showerror("Error", "Please enter a nickname.")
            return
        print(f"Nickname submitted: {nickname}")
        self.open_chat_window(nickname)
        self.signup_window.destroy()
    def open_chat_window(self, nickname):
        self.chat_window = ChatWindow(self.parent,nickname)
class ChatWindow:
    def __init__(self,parent,nickname):
        self.parent = parent
        self.nickname = nickname
        self.chat_window = tk.Toplevel(parent)
        self.chat_window.title("Chat")
        self.chat_window.configure(bg="#05053B")
        self.chat_window.geometry("1000x700")
        self.label = tk.Label(self.chat_window, text="Chat Screen", font=("Arial", 24),bg="#05053B",fg="#22B9FF")
        self.label.pack(pady=20)

        center_window(self.chat_window)
        self.chat_window.focus_force()
        self.greeting_label = tk.Label(
            self.chat_window,
            text=f"Welcome, {self.nickname}!",
            font=("Arial", 18),
            bg="#05053B",
            fg="#22B9FF",
            justify="left")
        self.greeting_label.pack(pady=10, anchor="w", padx=100)

        self.refresh_button = tk.Button(
            self.chat_window, 
            text="Refresh",
            font=("Arial", 18),
            command=self.refresh_chat)
        self.refresh_button.pack(pady=10, anchor="w", padx=125)

        self.users_online = tk.Listbox(
            self.chat_window,
            font=("Arial", 14),
            bg="#2D5961",
            fg="#22B9FF")
        self.users_online.pack(pady=20, anchor="w", padx=100-25)
        self.users_online.insert(tk.END, "User1")
        self.users_online.insert(tk.END, "User2")

        self.users_online.bind("<<ListboxSelect>>", self.on_user_select)
    
    def on_user_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            value = event.widget.get(index)
            print("Selected user:", value)
            #TODO: open new working chat window with selected user, cyber methods after
            
    def refresh_chat(self):
        print("to be implemented...")

CyberApp().run()