import os
import cv2
import time
import numpy as np
import threading
import telebot
from telebot import types
from ultralytics import YOLO

model = YOLO("../models/new_idea_ppe.pt")

INV_NAMES = {v: k for k, v in model.names.items()}
HAT_CLS = INV_NAMES.get("hat")
PERSON_CLS = INV_NAMES.get("person")

global_frames = {}
active_violations_event_list = []

def inside_box(point, box):
    x, y = point
    x1, y1, x2, y2 = box
    head_bottom = y1 + (y2 - y1) * 0.5
    return x1 < x < x2 and y1 < y < head_bottom

class CameraStreamWorker(threading.Thread):
    def __init__(self, camera_id, video_path, bot_token, chat_id, app_context):
        super().__init__()
        self.camera_id = camera_id
        self.video_path = video_path
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.app_context = app_context
        self.stopped = False

        self.violations = {}
        self.alerted = set()

        self.bot = telebot.TeleBot(self.bot_token) if self.bot_token else None
        cap_info = cv2.VideoCapture(self.video_path)
        fps = cap_info.get(cv2.CAP_PROP_FPS)
        cap_info.release()

        if fps == 0 or np.isnan(fps) or fps is None:
            fps = 30
        self.max_frames = fps*5


    def send_alert(self, sending_frames_list, person_id):
        if not self.bot or not self.chat_id:
            return
        
        def send_logic():
            try:
                media_group = []
                for i, frame in enumerate(sending_frames_list):
                    ret, enc_img = cv2.imencode('.jpg', frame)
                    if ret:
                        image_bytes = enc_img.tobytes()
                    if i == 0:
                        media_group.append(types.InputMediaPhoto(image_bytes, caption=f"⚠️ ALERT! Worker {person_id} has no helmet! (Camera ID: {self.camera_id})"))
                    else:
                        media_group.append(types.InputMediaPhoto(image_bytes))
                if media_group:
                    self.bot.send_media_group(self.chat_id, media_group)
            except Exception as e:
                return
        
        threading.Thread(target=send_logic).start()

    
    def save_violation_to_db(self, cropped_frame, full_frame, person_id):
        from extensions import db
        from models import Violation, Camera
        import uuid
        from datetime import datetime, timezone

        base_dir = os.path.dirname(os.path.abspath(__file__))
        violations_dir = os.path.join(base_dir, 'static', 'uploads', 'violations')
        os.makedirs(violations_dir, exist_ok=True)

        unique_id = uuid.uuid4().hex
        crop_name = f"crop_{self.camera_id}_{person_id}_{unique_id}.jpg"
        full_name = f"full_{self.camera_id}_{person_id}_{unique_id}.jpg"

        crop_path = f"app/static/uploads/violations/{crop_name}"
        full_path = f"app/static/uploads/violations/{full_name}"

        cv2.imwrite(crop_path, cropped_frame)
        cv2.imwrite(full_path, full_frame)

        with self.app_context:
            try:
                camera = db.session.get(Camera, self.camera_id)
                if camera:
                    new_violation = Violation(
                        camera_id=self.camera_id,
                        person_id=person_id,
                        violation_type="Helmet Missing",
                        cropped_path=crop_path,
                        full_frame_path=full_path,
                        user_id=camera.user_id
                    )
                    db.session.add(new_violation)
                    db.session.commit()

                    now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
                    active_violations_event_list.append({
                        "camera_name" : camera.name,
                        "person_id": person_id,
                        "time": now_str,
                        "type": "Helmet Missing"
                    })
            except Exception as e:
                db.session.rollback()


    def run(self):
        print("running lol")

        results_stream = model.track(
            source=self.video_path,
            persist=True,
            tracker="bytetrack.yaml",
            show=False,
            verbose=False,
            stream=True,
            device=0
        )

        for result in results_stream:
            if self.stopped:
                break

            frame = result.orig_img
            boxes = result.boxes

            if boxes is None or len(boxes) == 0:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    global_frames[self.camera_id] = jpeg.tobytes()
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

                    if p_id not in self.violations:
                        self.violations[p_id] = 1
                    else:
                        self.violations[p_id] += 1
                        if self.violations[p_id] > self.max_frames and p_id not in self.alerted:
                            
                            h, w = frame.shape[:2]
                            y1_c, y2_c = max(0, y1), min(h, y2)
                            x1_c, x2_c = max(0, x1), min(w, x2)
                            cropped_frame = frame[y1_c:y2_c, x1_c:x2_c]
                            sending_frames_list = [cropped_frame, frame]

                            self.send_alert(sending_frames_list, p_id)
                            self.save_violation_to_db(cropped_frame, frame, p_id)

                            self.alerted.add(p_id)
                else:
                    color = (0, 255, 0)
                    self.violations.pop(p_id, None)
                    self.alerted.discard(p_id)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"ID:{p_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            current_frame_ids = {p_id for p_id, _ in person_id_coords}
            for old_id in list(self.violations.keys()):
                if old_id not in current_frame_ids:
                    self.violations.pop(old_id, None)
                    self.alerted.discard(old_id)

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                global_frames[self.camera_id] = jpeg.tobytes()
                time.sleep(0.01)


    def stop(self):
        self.stopped = True