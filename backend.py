import cv2
from ultralytics import YOLO
import time

model = YOLO("new_idea_ppe.pt")
video_path = "test_images/testvideo.mp4"

violations = {}
alerted = set()

def inside_box(point, box):
    x, y = point
    x1, y1, x2, y2 = box
    head_bottom = y1 + (y2 - y1) * 0.35
    return x1 < x < x2 and y1 < y < head_bottom

results_stream = model.track(source=video_path,
                        persist=True,
                        tracker="botsort.yaml",
                        show=False,
                        verbose=False,
                        stream=True
                        )

for result in results_stream:
    frame = result.orig_img

    helmet_centers = []
    person_id_coords = []

    boxes = result.boxes
    for box in boxes:
        class_id = int(box.cls.item())
        class_name = model.names[class_id]

        if class_name == "hat":
            xywh = box.xywh[0].tolist()
            cx = xywh[0]
            cy = xywh[1]
            helmet_centers.append((cx, cy))
        
        elif class_name == "person":
            person_id = int(box.id.item()) if box.id is not None else None
            if person_id is not None:
                xyxy = box.xyxy.tolist()[0]
                x1, y1, x2, y2 = map(int, xyxy[:4])
                person_id_coords.append((person_id, (x1, y1, x2, y2)))

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

    current_time = time.time()

    for p_id, p_box in person_id_coords:
        x1, y1, x2, y2 = p_box

        if not has_helmet[p_id]:
            color = (0, 0, 255)

            if p_id not in violations:
                violations[p_id] = current_time
            else:
                elapsed = current_time - violations[p_id]
                if elapsed > 5 and p_id not in alerted:
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