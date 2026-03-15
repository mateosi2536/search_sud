import json
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from tqdm import tqdm
import torch

# Rutas actualizadas según tu reorganización
input_path = r'C:\Users\mateo\Desktop\cuadruple\chunks\scripture_chunks.jsonl'
output_path = r'C:\Users\mateo\Desktop\cuadruple\chunks\scriptures_with_vectors_f16.json'

def generate():
    if not os.path.exists(input_path):
        print(f"Error: No se encontró el archivo de entrada en {input_path}")
        return

    # Modelo multilingüe 768 dims — más preciso, soporta hasta 512 tokens por chunk
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Dispositivo: {device.upper()} {'(' + torch.cuda.get_device_name(0) + ')' if device == 'cuda' else '(sin GPU disponible)'}")
    print("Cargando modelo: paraphrase-multilingual-mpnet-base-v2 (768 dimensiones)...")
    model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2', device=device)

    print("Leyendo chunks...")
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    chunks = [json.loads(line) for line in lines]
    print(f"Total de chunks a procesar: {len(chunks)}")

    texts = [c['text'] for c in chunks]

    print("Generando embeddings (esto tomará un momento)...")
    # Generamos los vectores
    embeddings = model.encode(texts, batch_size=128, show_progress_bar=True, convert_to_numpy=True)

    print("Convirtiendo vectores a Float16 (16 bits) para optimizar espacio (768 dims)...")
    # Convertimos a float16
    embeddings_f16 = embeddings.astype(np.float16)

    print("Asociando vectores a los chunks...")
    for i, chunk in enumerate(chunks):
        # Guardamos el vector como lista para el JSON
        chunk['vector'] = embeddings_f16[i].tolist()

    # Aseguramos que el directorio de salida existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Guardando archivo final en {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False)

    print("¡Hecho! Base de datos preparada con vectores de 768 dimensiones en 16 bits.")

if __name__ == "__main__":
    generate()
