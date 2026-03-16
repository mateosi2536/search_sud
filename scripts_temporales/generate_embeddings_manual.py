import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from tqdm import tqdm
import torch

input_path  = r'C:\Users\mateo\Desktop\cuadruple\chunks\manual_chunks.jsonl'
output_path = r'C:\Users\mateo\Desktop\cuadruple\chunks\manual_with_vectors_f16.json'

def generate():
    if not os.path.exists(input_path):
        print(f"Error: No se encontró {input_path}")
        print("Corre primero generate_chunks_manual.py")
        return

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    gpu_name = torch.cuda.get_device_name(0) if device == 'cuda' else 'sin GPU'
    print(f"Dispositivo: {device.upper()} ({gpu_name})")
    print("Cargando modelo: paraphrase-multilingual-mpnet-base-v2 (768 dims)...")
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device=device)

    print("Leyendo chunks...")
    with open(input_path, 'r', encoding='utf-8') as f:
        chunks = [json.loads(line) for line in f]
    print(f"Total chunks: {len(chunks)}")

    texts = [c['text'] for c in chunks]

    print("Generando embeddings...")
    embeddings = model.encode(
        texts,
        batch_size=128,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    print("Convirtiendo a Float16...")
    embeddings_f16 = embeddings.astype(np.float16)

    print("Asociando vectores...")
    for i, chunk in enumerate(chunks):
        chunk['vector'] = embeddings_f16[i].tolist()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Guardando en {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False)

    print(f"Listo. {len(chunks)} chunks con vectores de 768 dims (float16).")

if __name__ == "__main__":
    generate()
