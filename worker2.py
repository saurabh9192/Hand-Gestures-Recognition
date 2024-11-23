import cv2
import pandas as pd
from ultralytics import YOLO
from tracker import Tracker
from multiprocessing import Pipe
import time

def process_video(video_file, conn):
    model = YOLO('best.pt')
    tracker = Tracker()
    class_list = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']
    
    cap = cv2.VideoCapture(video_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    delay = int(1000/fps)

    down = set()
    counter_down = []
    
    cap = cv2.VideoCapture(video_file)
    
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (1120, 700))
        results = model.predict(frame)
        detections = results[0].boxes.data.detach().cpu().numpy()
        px = pd.DataFrame(detections).astype("float")
        
        objects = []
        for _, row in px.iterrows():
            x1, y1, x2, y2, _, cls_id = map(int, row[:6])
            label = class_list[cls_id]
            if 'car' in label or 'bus' in label or 'truck' in label:
                objects.append([x1, y1, x2, y2])

        for obj in tracker.update(objects):
            x3, y3, x4, y4, obj_id = obj
            cy = (y3 + y4) // 2
            red_line_y = 360
            blue_line_y = 450
            offset = 10
            
            if red_line_y < (cy + offset) and red_line_y > (cy - offset):
                down.add(obj_id)
            
            if obj_id in down and blue_line_y < (cy + offset) and blue_line_y > (cy - offset):
                counter_down.append(obj_id)
                down.remove(obj_id)
        
        if time.time() - start_time >= 20:
            conn.send(len(counter_down))  # Send count to parent every 20 seconds
            counter_down = []  # Reset count after sending
            start_time = time.time()
        
        cv2.waitKey(delay)

    cap.release()
    conn.close()

if __name__ == "__main__":
    video_file = "Video_Highway2.mp4"  # Change this for each worker (e.g., worker2 uses "Video_Highway_2.mp4")
    parent_conn, child_conn = Pipe()
    process_video(video_file, child_conn)
