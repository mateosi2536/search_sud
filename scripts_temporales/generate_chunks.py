import json
import os
import glob

SPA_DIR    = r'C:\Users\mateo\Desktop\cuadruple\chunks\spa\spa'
OUTPUT     = r'C:\Users\mateo\Desktop\cuadruple\chunks\scripture_chunks.jsonl'

VOLUME_ES = {
    'Old Testament':        'Antiguo Testamento',
    'New Testament':        'Nuevo Testamento',
    'Book of Mormon':       'Libro de Mormón',
    'Doctrine and Covenants': 'Doctrina y Convenios',
    'Pearl of Great Price': 'Perla de Gran Precio',
}

# Orden canónico de los volúmenes para procesar los libros en secuencia correcta
VOLUME_ORDER = [
    'Old Testament',
    'New Testament',
    'Book of Mormon',
    'Doctrine and Covenants',
    'Pearl of Great Price',
]

CENTRAL = 3  # versos centrales por chunk (paso)
MARGIN  = 1  # versos de margen a cada lado

def process_chapter(verses):
    """Divide el capítulo en grupos de CENTRAL versos, cada uno expandido con MARGIN a cada lado."""
    chunks = []
    n = len(verses)

    for i in range(0, n, CENTRAL):
        win_start = max(0, i - MARGIN)
        win_end   = min(n, i + CENTRAL + MARGIN)
        window    = verses[win_start:win_end]

        text = ' '.join(f"[V{v['verse_number']}] {v['scripture_text']}" for v in window)
        chunks.append({
            'chunk_id': f"{window[0]['book_title']}-{window[0]['chapter_number']}-{window[0]['verse_number']}-{window[-1]['verse_number']}",
            'text': text,
            'metadata': {
                'volume': VOLUME_ES.get(window[0]['volume_title'], window[0]['volume_title']),
                'book':    window[0]['book_title'],
                'chapter': window[0]['chapter_number'],
                'verses':  [v['verse_number'] for v in window],
            }
        })
    return chunks


def create_chunks():
    files = glob.glob(os.path.join(SPA_DIR, '*.json'))
    print(f"Archivos encontrados: {len(files)}")

    # Cargamos todos los libros y los agrupamos por volumen
    books_by_volume = {v: [] for v in VOLUME_ORDER}
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            book = json.load(f)
        vol = book['volume_title']
        if vol in books_by_volume:
            books_by_volume[vol].append(book)

    total_chunks = 0
    with open(OUTPUT, 'w', encoding='utf-8') as out:
        for vol in VOLUME_ORDER:
            books = sorted(books_by_volume[vol], key=lambda b: b['book_title'])
            for book in books:
                for chapter in book['chapters']:
                    verses = chapter['verses']
                    for chunk in process_chapter(verses):
                        out.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                        total_chunks += 1

    print(f"Chunks generados: {total_chunks}")
    print(f"Guardado en: {OUTPUT}")


if __name__ == '__main__':
    create_chunks()
