import tkinter as tk
import os
from PIL import Image, ImageTk
from main import App

class GUI0(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#FFFFFF", width=1280, height=832)
        self.pack_propagate(False)
        self.pack()
        self.master = master
        self.im_dir = f"{os.path.dirname(__file__)}/assets/gui0"
        self.canvas = tk.Canvas(self, bg="#FFFFFF", height=832, width=1280,
                                highlightthickness=0, relief="ridge")
        self.canvas.pack(fill="both", expand=True)
        self.init_static()
        self.after(4000, self.to_gui1)
        

    def init_static(self):
        self.image_image_1 = tk.PhotoImage(file=f"{self.im_dir}/image_1.png")
        self.canvas.create_image(
            640.0,
            416.0,
            image=self.image_image_1
        )

        self.image_image_2 = tk.PhotoImage(file=f"{self.im_dir}/image_2.png")
        self.canvas.create_image(
            640.0,
            633.0,
            image=self.image_image_2
        )

        self.image_image_3 = tk.PhotoImage(file=f"{self.im_dir}/image_3.png")
        self.canvas.create_image(
            639.0,
            678.0,
            image=self.image_image_3
        )

    def to_gui1(self):
        self.pack_forget()  # Ẩn GUI0
        app = App_(self.master)
        app.pack()

class App_(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="black", width=1280, height=832)
        self.pack_propagate(False)
        self.im_dir = f"{os.path.dirname(__file__)}/assets/gui1"
        self.canvas = tk.Canvas(self, bg="black", width=1280, height=832)
        self.canvas.pack(fill="both", expand=True)
        self.init_static()
    
    def init_static(self):
        self.image_image_1 = tk.PhotoImage(
            file=f"{self.im_dir}/image_2.png")
        self.canvas.create_image(
            640.0,
            416.0,
            image=self.image_image_1
        )

        self.start_icon = ImageTk.PhotoImage(Image.open("./assets/gui1/button_1.png"))
        self.start_button = self.canvas.create_image(200, 720, image=self.start_icon)
        self.canvas.tag_bind(self.start_button, "<Button-1>", lambda e: self.to_app())
    
    def to_app(self):
        print("ok")
        self.pack_forget()  # Ẩn GUI0
        app = App(self.master)
        app.pack()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1280x832")
    gui0 = GUI0(root)
    root.mainloop()
