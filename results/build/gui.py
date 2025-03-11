import tkinter as tk
import os
from PIL import Image, ImageTk

class ResultCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.im_dir = f"{os.path.dirname(__file__)}/assets/frame0"
        self.configure(bg="white")
        self.create_rectangle(0.0, 0.0, 425.0, 832.0, fill="#FFFFFF", outline="")
        self.create_text(40, 60.0, anchor="nw", text="Kết quả", fill="#535353", font=("Mulish Bold", 20, "bold"))
        self.init_canvas()
        # Chỉnh font chữ lớn hơn cho text "Áo"
        self.create_text(70, 640.0, anchor="nw", text="Màu áo", fill="#535353", font=("Mulish Bold", 20, "bold"))
        self.create_button()
    
    def init_canvas(self):
        render_left_texts = ["Họ và tên:", "Giới tính:", "Nametag:", "Mắt kính:" ,"Áo:","Cà vạt:"]
        for i,text in enumerate(render_left_texts):
            self.create_text(
                40,
                140.0 + i * 40,
                anchor="nw",
                text=text,
                fill="#535353",
                font=("Times New Roman", 18, "bold"),
            )

    def create_button(self):
        self.x_icon = ImageTk.PhotoImage(Image.open(f"{os.path.dirname(__file__)}/assets/frame0/x_icon2.png").resize((1,1)))
        self.x_icon_button = self.create_image(20, 20, image=self.x_icon)
        # self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: self.command)

    def asign_button(self, command):
        self.tag_bind(self.x_icon_button, "<Button-1>", lambda e: command())

    def render_result(self, res_json):
    # Khai báo các biến ban đầu
        im_name = ""
        glasses_position = ""
        nametag_text = ""
        shirt_color_text = ""
        tie_text = ""
        gender = ""
        
        # Khởi tạo màu mặc định cho từng item
        # Dùng "#00FF00" cho xanh và "#FF0000" cho đỏ
        im_color = "#00FF00"
        glasses_color = "#00FF00"
        nametag_color = "#00FF00"
        shirt_color_color = "#00FF00"
        tie_color = "#00FF00"
        gender_color = "#00FF00"  # Mặc định cho gender (không có comment cụ thể)

        # Xử lý face_id
        if "im_name" in res_json["face_id"]:
            gender = "Nam" if res_json["face_id"]["gender"] == "Man" else "Nữ"
            im_name = res_json["face_id"]["im_name"]
            # Nếu im_name là "Không tìm thấy trong cơ sở dữ liệu" => tô đỏ, ngược lại => tô xanh
            if im_name == "Không tìm thấy trong cơ sở dữ liệu":
                im_name = "Không tìm thấy trong CSDL"
                im_color = "#FF0000"
            else:
                im_color = "#00FF00"

        # Xử lý glasses
        if len(res_json["glasses"]) > 0:
            pos = res_json["glasses"][0]["position"]
            if pos == "Wearing":
                glasses_position = "Mang mắt kính trên mắt"
            elif pos == "Head":
                glasses_position = "Mang mắt kính trên đầu"
            elif pos == "Pocket":
                glasses_position = "Mang mắt kính ở ngực"
            glasses_color = "#00FF00"  # Xác định được vị trí => xanh
        else:
            glasses_position = "Không đeo mắt kính"
            glasses_color = "#FF0000"  # Không có => đỏ

        # Xử lý nametag
        if len(res_json["nametag"]) > 0:
            nametag_text = "Mang nametag đúng quy định"
            nametag_color = "#00FF00"  # Đúng quy định => xanh
        else:
            nametag_text = "Không mang nametag"
            nametag_color = "#FF0000"  # Sai quy định => đỏ

        # Xử lý màu áo (shirt/dress)
        if len(res_json["shirt_color"]) > 0 or len(res_json.get("dress_color", [])) > 0:
            shirt_color_text = "Đã xác định được màu áo"
            shirt_color_color = "#00FF00"  # Xác định được => xanh
        else:
            shirt_color_text = "Không xác định được màu áo"
            shirt_color_color = "#FF0000"  # Không xác định => đỏ

        # Xử lý cà vạt (tie)
        if gender == "Nam":
            if len(res_json["tie"]) > 0:
                tie_text = "Có mang cà vạt"
                tie_color = "#00FF00"  # Có => xanh
            else:
                tie_text = "Không mang cà vạt"
                tie_color = "#FF0000"  # Không có => đỏ
        else:
            tie_text = "N/A"
            tie_color = "#FF0000"  # Nữ => đỏ

        # Tạo danh sách kết quả kèm theo màu tương ứng
        results = [
            (im_name, im_color),
            (gender, gender_color),
            (nametag_text, nametag_color),
            (glasses_position, glasses_color),
            (shirt_color_text, shirt_color_color),
            (tie_text, tie_color),
        ]

        # Vẽ text với kích cỡ font 20 như comment (có thể điều chỉnh theo nhu cầu)
        for i, (text, color) in enumerate(results):
            self.create_text(
                190,
                140.0 + i * 40,
                anchor="nw",
                text=text,
                fill=color,
                font=("Times New Roman", 18),
                tags="result_text"
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
