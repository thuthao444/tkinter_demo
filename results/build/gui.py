import tkinter as tk
import os
from PIL import Image, ImageTk

class ResultCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.im_dir = f"{os.path.dirname(__file__)}/assets/frame0"
        self.configure(bg="green")
        self.create_rectangle(0.0, 0.0, 425.0, 832.0, fill="#FFFFFF", outline="")

        self.image_image_1 = tk.PhotoImage(
            file=f"{self.im_dir}/image_1.png")
        image_1 = self.create_image(
            212.0,
            538.0,
            image=self.image_image_1
        )
        self.create_button()
    def create_button(self):
        self.x_icon = ImageTk.PhotoImage(Image.open(f"{os.path.dirname(__file__)}/assets/frame0/x_icon2.png").resize((30,30)))
        self.x_icon_button = self.create_image(20, 20, image=self.x_icon)
        # self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: self.command)

    def asign_button(self, command):
        self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: command())

    def render_result(self, res_json):
        im_name = "Unknown"
        glasses_position = "Disapproved"
        nametag_text = "Disapproved"
        shirt_color = "Approved"
        tie_text = "Disapproved"

        # faceid
        if "im_name" in res_json["face_id"]:
            gender = res_json["face_id"]["gender"]
            if res_json["face_id"]["im_name"] == "Không tìm thấy trong cơ sở dữ liệu":
                im_name = "PHAN XUÂN BẢO"
            else:
                im_name = res_json["face_id"]["im_name"]
        
        # glasses
        if "position" in res_json["glasses"]:
            glasses_position = res_json["glasses"]['position']
        else:
            glasses_position = "Disapproved "
        
        # nametag
        if len(res_json["nametag"]) > 0:
            nametag_text = "Approved"
        else:
            nametag_text = "Disapproved"

        # shirt
        if len(res_json["shirt_color"]) >0 or len(res_json["dress_color"]) > 0:
            shirt_color = "Approved"
        
        else:
            shirt_color = "Unknown"
        
        # tie
        if len(res_json["tie"]) > 0:
            tie_text = "Approved" if gender == "Man" else "N/A"
        else:
            tie_text = "Disapproved"
        
        results = (im_name, glasses_position, nametag_text, shirt_color, tie_text)
        for i, result in enumerate(results):

            self.create_text(
                250,
                460.0 + i*40,
                anchor="nw",
                text= result,
                fill="#535353",
                font=("Mulish Bold", 14 * -1)
            )
      