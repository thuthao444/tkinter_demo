from pathlib import Path
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage
from PIL import Image, ImageTk
import os, cv2
import tkinter as tk
import requests, uuid
import time
from main import App

class GUI0:
    def __init__(self, window):
        self.im_dir = f"{os.path.dirname(__file__)}/assets/gui0"
        self.window = window
        self.window.geometry("1280x832")
        self.window.configure(bg="#FFFFFF")

        self.canvas = Canvas(
            self.window,
            bg="#FFFFFF",
            height=832,
            width=1280,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        self.init_static()

        # Instead of time.sleep, use after to schedule the transition
        self.window.after(1000, self.to_gui1)

    def to_gui1(self):
        app = App()
    def init_static(self):
        # Load images and create canvas items.
        self.image_image_1 = PhotoImage(file=f"{self.im_dir}/image_1.png")
        self.canvas.create_image(
            640.0,
            416.0,
            image=self.image_image_1
        )

        self.image_image_2 = PhotoImage(file=f"{self.im_dir}/image_2.png")
        self.canvas.create_image(
            640.0,
            633.0,
            image=self.image_image_2
        )

        self.image_image_3 = PhotoImage(file=f"{self.im_dir}/image_3.png")
        self.canvas.create_image(
            639.0,
            678.0,
            image=self.image_image_3
        )

        self.window.resizable(False, False)
        # Remove mainloop call from here!

if __name__ == "__main__":
    window = tk.Tk()
    app = GUI0(window)
    window.mainloop()
