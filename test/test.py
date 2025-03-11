import os
import httpx
import msgpack
import asyncio
import uuid
import cv2

async def fetch(client: httpx.AsyncClient, url: str, data: dict = None, files: dict = None, is_msg=False, result_path=None):
    def render_result(res_json):
        def draw_bounding_box(label, x1, y1, x2, y2, shirt=None):
            if label == "Không tìm thấy trong CSDL":
                label = "Khong tim thay trong CSDL"
            im = cv2.imread(result_path)
            im_result = cv2.rectangle(im, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if label is not None:
                im_result = cv2.putText(im_result, f"{label}", (x1,y1-20), cv2.FONT_HERSHEY_SIMPLEX,
                                        0.5, (255,0,0), 2, cv2.LINE_AA)
            
            if shirt is not None:       # shirt: [R,G,B]
                im_result = cv2.rectangle(im_result, (x1, y1), (x2, y2), shirt, -1)
            cv2.imwrite(result_path, im_result)
        
        if "im_name" in res_json["face_id"]:
            if res_json["face_id"]["im_name"] == "Không tìm thấy trong cơ sở dữ liệu":
                im_name = "Không tìm thấy trong CSDL"
            else:
                im_name = res_json["face_id"]["im_name"]
        else:
            im_name = "N/A"
        draw_bounding_box(im_name, res_json["face_id"]["x"], res_json["face_id"]["y"],
                        res_json["face_id"]["x"] + res_json["face_id"]["w"], 
                        res_json["face_id"]["y"] + res_json["face_id"]["h"])

        ######## Glasses #######
        if len(res_json["glasses"]) > 0:
            draw_bounding_box(None, *map(int, res_json["glasses"][0]["bounding_box"]))

        ######## Nametag ########
        if len(res_json["nametag"]) > 0:
            draw_bounding_box(None, *map(int, [res_json["nametag"][0]["x1"], res_json["nametag"][0]["y1"],res_json["nametag"][0]["x2"], res_json["nametag"][0]["y2"]]))

        ######## Tie ########
        if len(res_json["tie"]) > 0:
            draw_bounding_box(None, *map(int, [res_json["tie"][0]["x1"], res_json["tie"][0]["y1"],res_json["tie"][0]["x2"], res_json["tie"][0]["y2"]]))

        ####### shirt #######
        if len(res_json["shirt_color"]) > 0:
            shirt_color_value = list(map(int, res_json["shirt_color"]))
        elif len(res_json["dress_color"]) > 0:
            shirt_color_value = list(map(int, res_json["dress_color"]))
        else:
            shirt_color_value = [0,0,0]

        draw_bounding_box(None, 0, 0, 30, 30, [shirt_color_value[0], shirt_color_value[1], shirt_color_value[2]])
        

    response = await client.post(url, data=data, files=files)
    res_json = msgpack.unpackb(response.content) if is_msg else response.json()
    print("res_json", res_json)
    render_result(res_json)
    return msgpack.unpackb(response.content) if is_msg else response.json()

async def test_cloth():
    im_dir = "./glasses/Glasses"
    im_paths = [os.path.join(im_dir, im_name) for im_name in os.listdir(im_dir)]
    
    session_id = str(uuid.uuid4())
    tasks = []
    async with httpx.AsyncClient(timeout=None) as client:
        for im_path in im_paths:
            result_path = f"./result/{os.path.split(im_path)[1]}"
            cv2.imwrite(result_path, cv2.imread(im_path))
            with open(im_path, "rb") as f:
                file_tuple = (os.path.basename(im_path), f.read(), "image/png")
            files = {"front": file_tuple, "left": file_tuple, "right": file_tuple, "back": file_tuple}
            data = {"session_id": session_id}
            tasks.append(fetch(client, "http://100.86.165.5:8002/all", data=data, files=files, result_path=result_path))
        
        results = await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(test_cloth())
