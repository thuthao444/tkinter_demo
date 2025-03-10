import tkinter as tk
import os
from PIL import Image, ImageTk

class ResultCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.im_dir = f"{os.path.dirname(__file__)}/assets/frame0"
        self.configure(bg="green")
        self.create_rectangle(0.0, 0.0, 425.0, 832.0, fill="#FFFFFF", outline="")
        
        self.init_canvas()
        # Chỉnh font chữ lớn hơn cho text "Áo"
        self.create_text(110, 640.0, anchor="nw", text="Áo", fill="#535353", font=("Mulish Bold", 20, "bold"))
        self.create_button()
    
    def init_canvas(self):
        render_left_texts = ["Họ và tên:", "Giới tính:", "Nametag:", "Cà vạt:", "Mắt kính:", "Áo:"]
        for i,text in enumerate(render_left_texts):
            self.create_text(
                10,
                140.0 + i * 40,
                anchor="nw",
                text=text,
                fill="#535353",
                font=("Times New Roman", 20, "bold"),
                tags="result_text"  # Gán tag cho các text items
            )

    def create_button(self):
        self.x_icon = ImageTk.PhotoImage(Image.open(f"{os.path.dirname(__file__)}/assets/frame0/x_icon2.png").resize((1,1)))
        self.x_icon_button = self.create_image(20, 20, image=self.x_icon)
        # self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: self.command)

    def asign_button(self, command):
        self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: command())

    def render_result(self, res_json):
        im_name = ""
        glasses_position = ""
        nametag_text = ""
        shirt_color = ""
        tie_text = ""
        gender = ""

        # faceid
        if "im_name" in res_json["face_id"]:
            gender = "Nam" if res_json["face_id"]["gender"] == "Man" else "Nữ"
            im_name = res_json["face_id"]["im_name"]
        # glasses
        if len(res_json["glasses"]) > 0:
            if res_json["glasses"][0]["position"] == "Wearing":
                glasses_position = "Mang mắt kính trên mắt"
            if res_json["glasses"][0]["position"] == "Head":
                glasses_position = "Mang mắt kính trên đầu"
            if res_json["glasses"][0]["position"] == "Pocket":
                glasses_position = "Mang mắt kính ở ngực"
        else:
            glasses_position = "Không đeo mắt kính"
        
        # nametag
        if len(res_json["nametag"]) > 0:
            nametag_text = "Mang nametag đúng quy định"
        else:
            nametag_text = "Không mang nametag"

        # shirt
        if len(res_json["shirt_color"]) > 0 or len(res_json.get("dress_color", [])) > 0:
            shirt_color = "Đã xác định"
        else:
            shirt_color = "N/A"
        
        # tie
        if gender == "Nam":
            if len(res_json["tie"]) > 0:
                tie_text = "Có mang cà vạt"
            else:
                tie_text = "Không mang cà vạt"
        else:
            tie_text = "N/A"
        
        results = (im_name, gender, nametag_text, shirt_color, tie_text, glasses_position)
        for i, result in enumerate(results):
            # Chỉnh font chữ ở đây với kích cỡ 20 (có thể điều chỉnh theo nhu cầu)
            self.create_text(
                180,
                140.0 + i * 40,
                anchor="nw",
                text=result,
                fill="#535353",
                font=("Times New Roman", 20),
                tags="result_text"  # Gán tag cho các text items
            )
        
        def rgb_to_hex(rgb):
            return "#%02x%02x%02x" % rgb

        x1, y1, x2, y2 = 50, 500, 200, 600
        shirt_color_value = list(map(int, res_json["shirt_color"])) if res_json.get("shirt_color") else list(map(int, res_json.get("dress_color", [])))

        if len(shirt_color_value) >= 3:
            fill_color = rgb_to_hex((shirt_color_value[2], shirt_color_value[1], shirt_color_value[0]))
        else:
            raise ValueError("Invalid color data: Expected at least 3 values")

        self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")

    def reset_result(self):
        # Xóa tất cả các text items có tag "result_text"
        self.delete("result_text")
        
        def rgb_to_hex(rgb):
            return "#%02x%02x%02x" % rgb

        x1, y1, x2, y2 = 50, 500, 200, 600
        shirt_color = [255, 255, 255]  # Màu mặc định trắng

        if len(shirt_color) >= 3:
            fill_color = rgb_to_hex((shirt_color[2], shirt_color[1], shirt_color[0]))
        else:
            raise ValueError("Invalid color data: Expected at least 3 values")

        self.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline="")

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1320x853")  # Kích thước cửa sổ chính

    canvas = ResultCanvas(root)
    canvas.pack(fill="both", expand=True)

    # Dữ liệu giả để test
    sample_data = {
        "face_id": {"im_name": "person_1.jpg", "gender": "Man"},
        "glasses": [{"position": "Wearing"}],
        "nametag": [{}],
        "shirt_color": [255, 0, 0],  # Màu đỏ
        "tie": [{}]
    }

    canvas.render_result(sample_data)

    root.mainloop()
