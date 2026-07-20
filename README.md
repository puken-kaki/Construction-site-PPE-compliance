# Construction Site PPE Compliance Monitoring System

A real-time multi-camera PPE (Helmet) compliance monitoring system made for construction sites. The app allows safety managers to manage multiple cameras via RTSP links, run background processes for object tracking and receive violation alerts in Telegram through a bot.

# Features

* **Camera Management**: Easily add, view, update, or remove cameras through a simple dashboard that cleans up old data automatically.
* **Smooth Streaming**: Every camera runs independently in the background, making sure video feeds do not lag or slow down.
* **Person Tracking**: Uses Ultralytics YOLO26 and ByteTrack to detect people in the video feed and assigns a unique ID to each worker so they can be followed across frames.
* **Smart Helmet Detection**: Checks if workers are wearing helmets by specifically looking at the area right above their shoulders, preventing false alarms from random objects.
* **Fewer False Alerts**: Counts frames based on video speed and only triggers an alert if a worker is missing a helmet for more than 5 seconds straight.
* **Instant Telegram Alerts**: Sends a picture of the worker and the full scene to Telegram immediately without freezing or interrupting the live video.
* **Live Dashboard Updates**: Automatically updates the web page with new safety violations as they happen, without requiring a manual refresh.
* **Analytics Page**: Shows weekly and daily violation statistics along with compliance rate for easy understanding. 

# Technical Stack

* **Backend Framework**: Flask, Flask-SQLAlchemy, Flask-Bcrypt, Flask-Login
* **Frontend**: HTML5, HTMX, Tailwind CSS
* **Computer Vision**: Ultralytics YOLO26, ByteTrack, OpenCV
* **Alerts**: PyTelegramBotAPI (telebot)

# Detection Mechanism
<img width="862" height="884" alt="diagram-export-7-5-2026-12_12_11-AM" src="https://github.com/user-attachments/assets/e86ecc1e-c366-480f-ae8a-610e045382d4" />

# Local Installation

## 1. Repository setup
Clone the repository and navigate to the root directory:
```bash
git clone https://github.com/puken-kaki/Construction-site-PPE-compliance.git
cd Construction-site-PPE-compliance
```

## 2. Directory Structure
The application structure requires the trained model to be placed one directory level above the web application directory, as configured in video_processor.py:
```bash
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
