"""
Scraper del Manual General en espanol
Descarga cada capitulo desde churchofjesuschrist.org y genera
archivos JSON con estructura similar a los chunks de las escrituras.
"""

import json
import time
import re
import os
import sys
import requests
from bs4 import BeautifulSoup

# Fix encoding para Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://www.churchofjesuschrist.org"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "chunks", "spa", "manual")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es,en;q=0.9",
}

DELAY = 2.0  # segundos entre requests

# Lista completa de capítulos del Manual General (slugs extraídos del TOC oficial)
CHAPTERS = [
    "title-page",
    "summary-of-recent-updates",
    "0-introductory-overview",
    "1-work-of-salvation-and-exaltation",
    "2-supporting-individuals-and-families",
    "3-priesthood-principles",
    "4-leadership-in-the-church-of-jesus-christ",
    "5-general-and-area-leadership",
    "6-stake-leadership",
    "7",
    "8-elders-quorum",
    "9-relief-society",
    "10-aaronic-priesthood",
    "11-young-women",
    "12-primary",
    "13-sunday-school",
    "14-single-members",
    "15-seminaries-and-institutes",
    "16-living-the-gospel",
    "17-teaching-the-gospel",
    "18-priesthood-ordinances-and-blessings",
    "19-music",
    "20-activities",
    "21-ministering",
    "22-providing-for-temporal-needs",
    "23",
    "24",
    "25-temple-and-family-history-work",
    "26-temple-recommends",
    "27-temple-ordinances-for-the-living",
    "28",
    "29-meetings-in-the-church",
    "30-callings-in-the-church",
    "31",
    "32-repentance-and-membership-councils",
    "33-records-and-reports",
    "34-finances-and-audits",
    "35",
    "36-creating-changing-and-naming-new-units",
    "37-specialized-stakes-wards-and-branches",
    "38-church-policies-and-guidelines",
]


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    resp.encoding = "utf-8"  # forzar UTF-8 independientemente del header
    return BeautifulSoup(resp.text, "html.parser")


def parse_section_number(text: str) -> str:
    """Extrae el numero de seccion de un texto como '1.2.3 Titulo'."""
    match = re.match(r"^(\d+(?:\.\d+)*)\s*", text)
    return match.group(1) if match else ""


def parse_chapter(url: str, slug: str) -> dict | None:
    """Descarga y parsea un capitulo, retorna dict estructurado."""
    soup = get_soup(url)

    # Titulo del capitulo
    h1 = soup.find("h1")
    chapter_title = h1.get_text(strip=True) if h1 else slug

    # Numero de capitulo desde el title-number
    title_num_el = soup.find("p", class_="title-number")
    chapter_number_raw = title_num_el.get_text(strip=True).rstrip(".") if title_num_el else ""

    chapter_number = None
    if chapter_number_raw:
        try:
            chapter_number = int(chapter_number_raw)
        except ValueError:
            chapter_number = chapter_number_raw

    article = soup.find("article") or soup.find("div", class_="body-block") or soup.body
    if not article:
        print(f"  ! No se encontro contenido en {url}")
        return None

    sections = []
    current_section = None
    current_subsection = None

    # Iterar sobre todos los elementos del artículo en orden
    for el in article.find_all(["h2", "h3", "p", "ul", "ol"], recursive=True):
        tag = el.name

        # Evitar procesar elementos dentro de h1/header de capitulo
        if el.find_parent(["h1"]):
            continue

        if tag == "h2":
            text = el.get_text(strip=True)
            sec_num = parse_section_number(text)
            sec_title = re.sub(r"^\d+(?:\.\d+)*\s*", "", text).strip()
            current_section = {
                "section_number": sec_num,
                "section_title": sec_title,
                "subsections": [],
                "paragraphs": [],
            }
            sections.append(current_section)
            current_subsection = None

        elif tag == "h3":
            text = el.get_text(strip=True)
            sec_num = parse_section_number(text)
            sec_title = re.sub(r"^\d+(?:\.\d+)*\s*", "", text).strip()
            current_subsection = {
                "section_number": sec_num,
                "section_title": sec_title,
                "paragraphs": [],
            }
            if current_section is None:
                current_section = {
                    "section_number": "",
                    "section_title": "",
                    "subsections": [],
                    "paragraphs": [],
                }
                sections.append(current_section)
            current_section["subsections"].append(current_subsection)

        elif tag == "p":
            # Saltar title-number y headings
            if "title-number" in (el.get("class") or []):
                continue
            if el.find_parent(["h1", "h2", "h3", "header"]):
                continue

            text = el.get_text(separator=" ", strip=True)
            if not text:
                continue

            if current_subsection is not None:
                current_subsection["paragraphs"].append(text)
            elif current_section is not None:
                current_section["paragraphs"].append(text)
            else:
                # Parrafo introductorio antes de cualquier seccion
                if not sections:
                    current_section = {
                        "section_number": "",
                        "section_title": "Introduccion",
                        "subsections": [],
                        "paragraphs": [],
                    }
                    sections.append(current_section)
                current_section["paragraphs"].append(text)

        elif tag in ("ul", "ol"):
            # Saltar listas que esten dentro de otra lista ya procesada
            if el.find_parent(["ul", "ol"]):
                continue
            items = [li.get_text(separator=" ", strip=True) for li in el.find_all("li", recursive=False)]
            items = [i for i in items if i]
            if not items:
                continue
            combined = " | ".join(items)
            if current_subsection is not None:
                current_subsection["paragraphs"].append(combined)
            elif current_section is not None:
                current_section["paragraphs"].append(combined)

    # Limpiar secciones vacias
    for sec in sections:
        sec["subsections"] = [s for s in sec["subsections"] if s["paragraphs"]]
    sections = [s for s in sections if s["paragraphs"] or s["subsections"]]

    return {
        "manual_title": "Manual General",
        "manual_title_short": "manual-general",
        "chapter_number": chapter_number,
        "chapter_slug": slug,
        "chapter_title": chapter_title,
        "sections": sections,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total = len(CHAPTERS)
    success = 0
    failed = []

    for i, slug in enumerate(CHAPTERS, 1):
        out_path = os.path.join(OUTPUT_DIR, f"{slug}.json")

        if os.path.exists(out_path):
            print(f"[{i}/{total}] Saltando (ya existe): {slug}")
            success += 1
            continue

        url = f"{BASE_URL}/study/manual/general-handbook/{slug}?lang=spa"
        print(f"[{i}/{total}] Descargando: {slug}")
        try:
            data = parse_chapter(url, slug)
            if data:
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                sec_count = len(data["sections"])
                title = data["chapter_title"]
                print(f"  OK [{sec_count} secciones] {title}")
                success += 1
            else:
                failed.append(slug)
        except Exception as e:
            print(f"  FAIL {slug}: {e}")
            failed.append(slug)

        if i < total:
            time.sleep(DELAY)

    print(f"\n{'='*50}")
    print(f"Completado: {success}/{total} capitulos")
    if failed:
        print(f"Fallidos ({len(failed)}): {', '.join(failed)}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
