
import cv2
import time
import threading
from queue import Queue
from pathlib import Path

from config import Config
from logger import logger
from utils import load_known_faces, init_item_db
from update_visitors import update_visitors

# Import Speech Modules
from speech.listener import speech_listener
from speech.handler import handle_speech_input

# Import Models
from models.insightface_model import face_model, recognize_face, draw_box

class VideoAgent:
    def __init__(self):
        logger.info("Initializing Video Agent...")
        
        # Ensure directories and files exist
        Config.ensure_directories()
        if not Config.VISITOR_LOG_PATH.exists():
            Config.VISITOR_LOG_PATH.touch()

        # Load Data
        self.known_faces = load_known_faces(Config.EMBEDDINGS_DIR)
        init_item_db()
        
        # Initialize State
        self.active_visitors = {}
        self.running = False
        
        # Queues and Events
        self.audio_queue = Queue()
        self.frame_request_queue = Queue()
        self.frame_response_queue = Queue()
        self.pause_listener_event = threading.Event()
        
        # Threads
        self.listener_thread = threading.Thread(
            target=speech_listener, 
            args=(self.audio_queue, self.pause_listener_event), 
            daemon=True,
            name="SpeechListener"
        )
        self.handler_thread = threading.Thread(
            target=handle_speech_input,
            args=(
                self.audio_queue, 
                self.pause_listener_event, 
                self.frame_request_queue, 
                self.frame_response_queue
            ),
            daemon=True,
            name="SpeechHandler"
        )

    def start(self):
        """
        Starts the agent's threads and main video loop.
        """
        logger.info("Starting Video Agent threads...")
        self.listener_thread.start()
        self.handler_thread.start()
        
        self.display_loop()

    def display_loop(self):
        """
        Main video capture and processing loop.
        """
        logger.info(f"Opening camera index {Config.CAMERA_INDEX}...")
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        if not cap.isOpened():
            logger.error(f"Cannot open camera {Config.CAMERA_INDEX}")
            return

        # Optional: Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_FRAME_HEIGHT)

        logger.info("Video Agent is running. Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to grab compressed frame.")
                    time.sleep(0.1)
                    continue

                # Mirror frame
                frame = cv2.flip(frame, 1)

                # Face Recognition
                names = []
                try:
                    faces = face_model.get(frame)
                    for face in faces:
                        emb = face.normed_embedding
                        name, sim = recognize_face(emb, self.known_faces, Config.FACE_RECOG_THRESHOLD)
                        frame = draw_box(face, name, sim, frame)
                        names.append(name)
                except Exception as e:
                    logger.error(f"Face recognition error: {e}")

                # Update Visitors Log
                self.active_visitors = update_visitors(
                    names, 
                    self.active_visitors, 
                    str(Config.VISITOR_LOG_PATH), 
                    grace_period_sec=20
                )

                # Handle Frame Requests from Agents
                if not self.frame_request_queue.empty():
                    req = self.frame_request_queue.get()
                    if req == "CAPTURE":
                        # Send copy of frame (numpy array) to avoid threading issues
                        self.frame_response_queue.put(frame.copy())
                    elif req == "get_frame":
                        # Legacy/Web support
                        _, jpeg = cv2.imencode(".jpg", frame)
                        frame_bytes = jpeg.tobytes()
                        self.frame_response_queue.put(frame_bytes)

                # Display
                cv2.imshow("Video Agent", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                    
        except KeyboardInterrupt:
            logger.info("Interrupted by user.")
        finally:
            self.stop(cap)

    def stop(self, cap):
        """
        Cleanup resources.
        """
        logger.info("Stopping Video Agent...")
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        logger.info("Goodbye!")
