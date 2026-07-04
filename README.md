## Construction Site PPE Compliance Monitoring System

A real-time, multi-camera PPE (Helmet) compliance monitoring system designed for industrial environments. The application enables safety managers to manage multiple camera streams via custom RTSP links, run independent background worker threads for real-time object tracking, and receive automated violation alerts directly in Telegram.

## Features

* **Multi-Camera Management**: Complete CRUD interface to register, stream, and terminate camera monitoring workers with automated database resource cleanup.
* **Isolated Multi-Threading Architecture**: Each active camera runs on its own dedicated CameraStreamWorker thread, preventing frame drops and isolating processing overhead.
* **Object Tracking**: Integrates Ultralytics YOLO with ByteTrack to assign persistent tracking IDs to individual workers across video frames.
* **Spatial Violation Logic**: Implements a custom bounding box overlap algorithm (inside_box) that validates helmet presence specifically in the upper head region of the detected person.
* **Temporal Thresholding**: Evaluates the stream frame rate dynamically and triggers violations only if a worker is missing a helmet for more than 5 consecutive seconds (max_frames), reducing false positives.
* **Asynchronous Media Alerts**: Compiles a media group containing both the cropped worker profile and the full frame, dispatching it asynchronously via the Telegram Bot API to avoid blocking the main processing loop.
* **Reactive Frontend Polling**: Fetches and renders live violation events dynamically using localized HTMX polling via the /api/live_violations endpoint.

## Tech Stack

* **Backend Framework**: Flask, Flask-SQLAlchemy, Flask-Bcrypt, Flask-Login
* **Frontend**: HTML5, HTMX, Tailwind CSS
* **Computer Vision**: Ultralytics YOLO26, ByteTrack, OpenCV (cv2)
* **Alert Integration**: PyTelegramBotAPI (telebot)

## Detection Mechanism
<img width="862" height="884" alt="diagram-export-7-5-2026-12_12_11-AM" src="https://github.com/user-attachments/assets/e86ecc1e-c366-480f-ae8a-610e045382d4" />

## Local Installation

## 1. Repository setup
Clone the repository and navigate to the root directory:
```bash
git clone https://github.com/puken-kaki/Construction-site-PPE-compliance.git
cd Construction-site-PPE-compliance
```

## 2. Directory Structure
The application structure requires the trained model to be placed one directory level above the web application directory, as configured in video_processor.py:
```text
├── models/
│   └── new_idea_ppe.pt
└── app/
    ├── app.py
    ├── video_processor.py
    ├── models.py
    ├── .env
    └── ...
```

## 3. Environment Setup
Create a virtual environment and install the required packages:
```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Mac and Linux
source venv/bin/activate

pip install -r requirements.txt
```

## 4. Configuration
Create a .env file in the directory level directly above app.py with the following variables:
```text
SECRET_KEY=your_flask_secret_key
BOT_TOKEN=your_telegram_bot_token
```

## 5. Running the Application
Execute the main script. The SQLite database file (site.db) will be initialized automatically inside the app/instance/ directory if it does not exist.
```bash
python app.py
```
The application will be accessible at http://127.0.0.1:5000.

## Model Weights

The trained model is not included in this repository due to file size.
