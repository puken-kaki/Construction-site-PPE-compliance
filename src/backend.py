import cv2
from ultralytics import YOLO
import numpy as np
import os
from dotenv import load_dotenv
import telebot
from threading import Thread

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = telebot.TeleBot(BOT_TOKEN)

model = YOLO("../models/new_idea_ppe.pt")
video_path = "../test_images/testvideo2.mp4"

cap_info = cv2.VideoCapture(video_path)
fps = cap_info.get(cv2.CAP_PROP_FPS)
cap_info.release()

if fps == 0 or np.isnan(fps):
    fps=30

max_frames = fps*5

violations = {}
alerted = set()

INV_NAMES = {v: k for k, v in model.names.items()}
HAT_CLS = INV_NAMES.get("hat")
PERSON_CLS = INV_NAMES.get("person")

def send_alert(sending_frame, person_id):
    def send_logic():
        try:
            ret, enc_img = cv2.imencode('.jpg', sending_frame)
            if ret:
                image_bytes = enc_img.tobytes()
                bot.send_photo(CHAT_ID, image_bytes, caption=f"⚠️ Alert! Worker {person_id} has no helmet!")
        except Exception as e:
            print(e)
    Thread(target=send_logic).start()

def inside_box(point, box):
    x, y = point
    x1, y1, x2, y2 = box
    head_bottom = y1 + (y2 - y1) * 0.5
    return x1 < x < x2 and y1 < y < head_bottom

results_stream = model.track(source=video_path,
                        persist=True,
                        tracker="bytetrack.yaml",
                        show=False,
                        verbose=False,
                        stream=True,
                        device=0
                        )

for result in results_stream:
    frame = result.orig_img
    boxes = result.boxes

    #numpy (gathering data about persons and hats)
    if boxes is None or len(boxes) == 0:
        cv2.imshow("Analytics", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    cls_arr = boxes.cls.cpu().numpy()

    hat_mask = (cls_arr == HAT_CLS)
    person_mask = (cls_arr == PERSON_CLS) & (boxes.id != None)

    if np.any(hat_mask):
        hat_xywh = boxes.xywh[hat_mask].cpu().numpy()
        helmet_centers = hat_xywh[:, :2]
    else:
        helmet_centers = []

    if np.any(person_mask):
        person_xyxy = boxes.xyxy[person_mask].cpu().numpy().astype(int)
        person_ids = boxes.id[person_mask].cpu().numpy().astype(int)
        person_id_coords = list(zip(person_ids, person_xyxy))
    else:
        person_id_coords = []
        person_ids = []

    has_helmet = {p_id: False for p_id, _ in person_id_coords}

    for helmet in helmet_centers:
        best_person = None
        best_distance = float("inf")

        for p_id, p_box in person_id_coords:
            if inside_box(helmet, p_box):
                x1, y1, x2, y2 = p_box
                hx = (x1 + x2) / 2
                hy = y1 + (y2 - y1) * 0.15

                dist = ((helmet[0]-hx)**2 + (helmet[1]-hy)**2)

                if dist < best_distance:
                    best_distance = dist
                    best_person = p_id

        if best_person is not None:
            has_helmet[best_person] = True

    for p_id, p_box in person_id_coords:
        x1, y1, x2, y2 = p_box

        if not has_helmet[p_id]:
            color = (0, 0, 255)

            if p_id not in violations:
                violations[p_id] = 1
            else:
                violations[p_id] += 1
                if violations[p_id] > max_frames and p_id not in alerted:
                    send_alert(frame, p_id)
                    print("VIOLATION!!!")
                    alerted.add(p_id)
        else:
            color = (0, 255, 0)
            violations.pop(p_id, None)
            alerted.discard(p_id)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"ID:{p_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    current_frame_ids = {p_id for p_id, _ in person_id_coords}
    for old_id in list(violations.keys()):
        if old_id not in current_frame_ids:
            violations.pop(old_id, None)
            alerted.discard(old_id)

    cv2.imshow("Analytics", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()