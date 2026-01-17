import os
import cv2
import numpy as np
import insightface

# Prepare the model
model = insightface.app.FaceAnalysis(name='buffalo_s')
model.prepare(ctx_id=-1)  # CPU

def compute_average_embedding(image_folder):
    embeddings = []

    for file_name in os.listdir(image_folder):
        file_path = os.path.join(image_folder, file_name)
        img = cv2.imread(file_path)
        if img is None:
            print(f"Failed to read {file_path}")
            continue

        faces = model.get(img)
        if faces:
            embedding = faces[0].normed_embedding
            embeddings.append(embedding)
            print(f"Got embedding from {file_name}")
        else:
            print(f"No face detected in {file_name}")

    if len(embeddings) == 0:
        raise ValueError(f"No embeddings found in {image_folder}")

    avg_embedding = np.mean(embeddings, axis=0)
    # Normalize the average to unit length
    avg_embedding /= np.linalg.norm(avg_embedding)
    return avg_embedding

print()

folders = os.listdir('./people')
for folder in folders:# Compute and save embeddings
    print(f'  -- Creating embeddings for {folder}  -- ')
    full_folder = os.path.join('people', folder)
    embed = compute_average_embedding(full_folder)
    np.save(f"./embeddings/{folder}_embedding.npy", embed)
    print()

print("Embeddings saved!")
