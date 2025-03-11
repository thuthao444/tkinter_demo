import requests
import os, cv2

ip_address = "http://localhost:8001/add_db"
im_dirs = "./"
for im_dir in os.listdir(im_dirs):
    if not im_dir.endswith(".py"):
        ims = {}
        for i, im_name in enumerate(os.listdir(im_dir)[:5]):
            im_path = os.path.join(im_dir, im_name)
            im_np = cv2.imread(im_path)
            if im_np is None:
                raise ValueError(f"Failed to read image: {im_path}")
            
            _, im_encoded = cv2.imencode(".png", im_np)
            im_bytes = im_encoded.tobytes()
            ims[f"im{i+1}"] = (im_name, im_bytes, "image/png")

        res = requests.post(ip_address, files=ims, data={"name":im_dir})
        res_json = res.json()
        print("res_json", res_json)

