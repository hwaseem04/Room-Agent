import cv2
import numpy as np
import insightface

# ====== Load model ======
face_model = insightface.app.FaceAnalysis(name='buffalo_s')
face_model.prepare(ctx_id=-1)  # -1 means CPU

# ====== Helper function ======
def recognize_face(embedding, known_faces, threshold=0.45):
    best_name = "Unknown"
    best_sim = 0

    for name, known_emb in known_faces.items():
        # Cosine similarity (dot product of L2-normalized embeddings)
        sim = np.dot(embedding, known_emb)
        if sim > best_sim:
            best_sim = sim
            best_name = name

    if best_sim >= threshold:
        return best_name, best_sim
    else:
        return "Unknown", best_sim
    
def draw_box(face, name, sim, frame):
    x1, y1, x2, y2 = face.bbox.astype(int)
    # Draw box
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # Draw name + similarity
    cv2.putText(frame, f"{name} {sim:.2f}", (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    return frame