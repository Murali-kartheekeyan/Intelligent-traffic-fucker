# analyzer/analyzer.py
# This module contains the core logic for video analysis, including frame capture.

import cv2
import time
import torch
import numpy as np
import os
import datetime

class VideoAnalyzer:
    """
    Handles video processing, object detection, frame generation, and periodic frame capture.
    """
    def __init__(self, video_path, traffic_light_controller):
        """
        Initializes the analyzer, loads the YOLOv5 model, and sets up the capture directory.
        """
        self.video_path = video_path
        self.traffic_light_controller = traffic_light_controller
        self.latest_analysis_data = {"vehicle_count": 0, "status": "Initializing..."}

        # --- Frame Capture Setup ---
        self.capture_dir = 'static/captured_frames'
        os.makedirs(self.capture_dir, exist_ok=True) # Create directory if it doesn't exist
        self.last_capture_time = time.time()
        self.capture_interval = 5  # Capture a frame every 5 seconds

        # --- YOLOv5 Model Loading ---
        try:
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
            self.model.eval()
            print("YOLOv5 model loaded successfully.")
        except Exception as e:
            print(f"Error loading YOLOv5 model: {e}")
            self.model = None

    def get_latest_analysis(self):
        """Returns the most recent analysis data."""
        return self.latest_analysis_data

    def _save_frame(self, frame):
        """Saves the given frame to the capture directory with a timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"capture_{timestamp}.jpg"
        filepath = os.path.join(self.capture_dir, filename)
        try:
            cv2.imwrite(filepath, frame)
            # print(f"Captured frame: {filename}")
        except Exception as e:
            print(f"Error saving frame {filename}: {e}")

    def process_frame(self, frame):
        """
        Processes a single frame to detect vehicles using the YOLOv5 model.
        """
        if self.model is None:
            return frame, {"vehicle_count": 0, "status": "Model not loaded"}

        results = self.model(frame)
        labels, cord = results.xyxyn[0][:, -1], results.xyxyn[0][:, :-1]
        
        vehicle_count = 0
        n = len(labels)
        x_shape, y_shape = frame.shape[1], frame.shape[0]

        for i in range(n):
            row = cord[i]
            label_id = int(labels[i])
            label_name = results.names[label_id]

            if label_name in ['car', 'motorcycle', 'bus', 'truck']:
                vehicle_count += 1
                x1, y1, x2, y2 = int(row[0]*x_shape), int(row[1]*y_shape), int(row[2]*x_shape), int(row[3]*y_shape)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label_name.capitalize(), (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        analysis_data = {"vehicle_count": vehicle_count, "status": "Processing"}
        self.latest_analysis_data = analysis_data
        
        return frame, analysis_data

    def generate_frames(self):
        """
        A generator function that reads a video, processes each frame, saves frames
        periodically, and yields the frame for streaming.
        """
        video_capture = cv2.VideoCapture(self.video_path)
        if not video_capture.isOpened():
            print(f"Error: Could not open video file at '{self.video_path}'.")
            return

        while True:
            success, frame = video_capture.read()
            if not success:
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            processed_frame, analysis_data = self.process_frame(frame.copy()) # Use a copy for drawing
            
            self.traffic_light_controller.update_logic_with_analysis(analysis_data)

            # --- Periodically save the processed frame ---
            current_time = time.time()
            if current_time - self.last_capture_time > self.capture_interval:
                self._save_frame(processed_frame)
                self.last_capture_time = current_time

            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1/30)

        video_capture.release()
