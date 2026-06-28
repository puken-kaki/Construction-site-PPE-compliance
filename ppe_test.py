#Testing on a video
import cv2
from ultralytics import YOLO

model = YOLO("PPE_FINALE_FINALE_BEST.pt")
cap = cv2.VideoCapture("test_images/testvideo.mp4")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model(frame)
    annotated_frame = results[0].plot()

    cv2.imshow("YOLO Detection", annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

#Testing on an image
'''
import cv2
from ultralytics import YOLO

model = YOLO("new_idea_ppe.pt")

image_path = "test_images/test.png"
results = model(image_path, conf=0.1, verbose=False)

result = results[0]
detected_helmets = []
detected_persons = []
for box in result.boxes:
    class_id = int(box.cls.item())
    print(class_id)
    if class_id == 0:
        detected_helmets.append(box)
    else:
        detected_persons.append(box)
print(f"People:{len(detected_persons)}, helmets:{len(detected_helmets)}")

annotated_image = result.plot()
cv2.imshow("YOLOv8 Detection", annotated_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
'''