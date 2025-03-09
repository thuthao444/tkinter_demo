import tkinter as tk
import os
from PIL import Image, ImageTk

class SessionCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.im_dir = f"{os.path.dirname(__file__)}/assets"
        self.configure(bg="orange")
        self.session_list = os.listdir(f"{os.path.dirname(__file__)}/gallery")[:16]
        self.place(x=0, y = 0)
        
        self.init_static()

    def init_static(self):

        self.create_rectangle(0.0, 0.0, 425.0, 832.0, fill="#FFFFFF", outline="")
        self.x_icon = ImageTk.PhotoImage(Image.open(f"{os.path.dirname(__file__)}/assets/x_icon2.png").resize((30,30)))
        self.x_icon_button = self.create_image(20, 20, image=self.x_icon)
        self.session_list_str_im = tk.PhotoImage(file=f"{self.im_dir}/button_1.png")
        self.create_image(212, 80, image=self.session_list_str_im)

        self.bounding_im = tk.PhotoImage(file=f"{self.im_dir}/image_1.png")
        self.create_image(212, 350, image=self.bounding_im)


        self.button_image_2 = tk.PhotoImage(file=f"{self.im_dir}/button_2.png")

        for i, session_name in enumerate(self.session_list):
            button_2 = tk.Button(
                self,
                image=self.button_image_2,
                text=session_name,
                compound="center",  # đặt text ở giữa image
                borderwidth=0,
                highlightthickness=0,
                command=lambda: self.view_session(f"{os.path.dirname(__file__)}/gallery/{session_name}"),
                relief="flat",
                font=("Mulish Regular", -14),
                fg="#000000"
            )

            self.create_window(70, 120 + i * 30, anchor="nw", window=button_2, width=300.0, height=25.0)

    def asign_button(self, command):
        self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: command())