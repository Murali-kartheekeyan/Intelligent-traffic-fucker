# app.py
# Main Flask application for the Intelligent Traffic Monitoring System.

from flask import Flask, render_template, Response, jsonify
from analyzer.analyzer import VideoAnalyzer
from traffic_logic.traffic_light import TrafficLightController
import os
import glob

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
VIDEO_FILE_PATH = 'static/videos/traffic.mp4'
CAPTURE_DIR = 'static/captured_frames'

# --- Initialize Modules ---
traffic_light_controller = TrafficLightController()
video_analyzer = VideoAnalyzer(video_path=VIDEO_FILE_PATH, traffic_light_controller=traffic_light_controller)


# --- Routes ---

@app.route('/')
def index():
    """Renders the main page of the application."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Provides the video stream to the web page."""
    return Response(video_analyzer.generate_frames(), 
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/traffic_light_status')
def traffic_light_status():
    """Provides the current status of the traffic light as a JSON object."""
    status = traffic_light_controller.get_state()
    return jsonify(status)

@app.route('/analysis_data')
def analysis_data():
    """Provides the latest analysis data (e.g., vehicle count) as a JSON object."""
    data = video_analyzer.get_latest_analysis()
    return jsonify(data)

@app.route('/get_captured_frames')
def get_captured_frames():
    """
    Scans the capture directory and returns a list of the most recent image filenames.
    """
    # Use glob to find all jpg files in the directory
    image_files = glob.glob(os.path.join(CAPTURE_DIR, '*.jpg'))
    
    # Sort files by modification time, newest first
    image_files.sort(key=os.path.getmtime, reverse=True)
    
    # Limit to the latest 12 frames to avoid cluttering the page
    latest_files = image_files[:12]
    
    # We only need the relative path for the web page (e.g., 'static/captured_frames/...')
    # Flask's url_for will handle the 'static' part, so we strip it.
    relative_paths = [os.path.join('captured_frames', os.path.basename(f)) for f in latest_files]
    
    return jsonify(relative_paths)


# --- Main Execution ---

if __name__ == '__main__':
    """Runs the Flask application."""
    app.run(debug=True, threaded=True)
