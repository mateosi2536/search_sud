import json
import os
import glob

MANUAL_DIR = r'C:\Users\mateo\Desktop\cuadruple\chunks\spa\manual'
OUTPUT     = r'C:\Users\mateo\Desktop\cuadruple\chunks\manual_chunks.jsonl'

CENTRAL = 3  # párrafos centrales por chunk
MARGIN  = 1  # párrafos de margen a cada lado


def collect_paragraphs(chapter: dict) -> list[dict]:
    """
    Aplana todas las secciones y subsecciones del capítulo
    en una lista de {section_number, section_title, text}.
    """
    paras = []
    ch_title = chapter.get('chapter_title', '')
    ch_num   = chapter.get('chapter_number', '')
    ch_slug  = chapter.get('chapter_slug', '')

    for sec in chapter.get('sections', []):
        sec_num   = sec.get('section_number', '')
        sec_title = sec.get('section_title', '')

        for p in sec.get('paragraphs', []):
            if p.strip():
                paras.append({
                    'chapter_number': ch_num,
                    'chapter_slug':   ch_slug,
                    'chapter_title':  ch_title,
                    'section_number': sec_num,
                    'section_title':  sec_title,
                    'text':           p.strip(),
                })

        for sub in sec.get('subsections', []):
            sub_num   = sub.get('section_number', '')
            sub_title = sub.get('section_title', '')
            for p in sub.get('paragraphs', []):
                if p.strip():
                    paras.append({
                        'chapter_number': ch_num,
                        'chapter_slug':   ch_slug,
                        'chapter_title':  ch_title,
                        'section_number': sub_num or sec_num,
                        'section_title':  sub_title or sec_title,
                        'text':           p.strip(),
                    })

    return paras


def make_chunks(paras: list[dict]) -> list[dict]:
    """Ventana deslizante de CENTRAL párrafos con MARGIN a cada lado."""
    chunks = []
    n = len(paras)

    for i in range(0, n, CENTRAL):
        win_start = max(0, i - MARGIN)
        win_end   = min(n, i + CENTRAL + MARGIN)
        window    = paras[win_start:win_end]

        # Construir texto con contexto de sección
        first = window[0]
        ctx = f"[{first['chapter_title']}]"
        if first['section_title']:
            ctx += f" [{first['section_title']}]"

        body = ' '.join(p['text'] for p in window)
        full_text = f"{ctx} {body}"

        chunk_id = (
            f"manual-{first['chapter_slug']}"
            f"-{first['section_number'] or 'intro'}"
            f"-p{i+1}"
        )

        chunks.append({
            'chunk_id': chunk_id,
            'text': full_text,
            'metadata': {
                'manual':          'Manual General',
                'chapter_number':  first['chapter_number'],
                'chapter_slug':    first['chapter_slug'],
                'chapter_title':   first['chapter_title'],
                'section_number':  first['section_number'],
                'section_title':   first['section_title'],
            }
        })

    return chunks


def create_chunks():
    files = sorted(glob.glob(os.path.join(MANUAL_DIR, '*.json')))
    print(f"Archivos encontrados: {len(files)}")

    total_chunks = 0
    with open(OUTPUT, 'w', encoding='utf-8') as out:
        for filepath in files:
            with open(filepath, 'r', encoding='utf-8') as f:
                chapter = json.load(f)

            paras = collect_paragraphs(chapter)
            if not paras:
                print(f"  ! Sin párrafos: {os.path.basename(filepath)}")
                continue

            for chunk in make_chunks(paras):
                out.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                total_chunks += 1

            print(f"  {os.path.basename(filepath)}: {len(paras)} párrafos → {len(make_chunks(paras))} chunks")

    print(f"\nTotal chunks generados: {total_chunks}")
    print(f"Guardado en: {OUTPUT}")


if __name__ == '__main__':
    create_chunks()
