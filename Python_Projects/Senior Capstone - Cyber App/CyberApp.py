#TODO: Main screen will have button to open new window - new window must have nickname config as well as texting functionality - 
#texting functionality comes first, must be encrypted
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
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

    def on_button_click(self):
        SignupWindow()
    def run(self):
        self.startup_window.mainloop()

class SignupWindow:
    def __init__(self):
        self.signup_window = tk.Toplevel()
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
    def submit_nickname(self):
        nickname = self.nickname_entry.get()
        if not nickname:
            tk.messagebox.showerror("Error", "Please enter a nickname.")
            return
        print(f"Nickname submitted: {nickname}")
        self.signup_window.destroy()
    #TODO: Find a way to transition from signup window destroyed to a chatting screen
CyberApp().run()