import { readFile, writeFile } from 'fs/promises';
import { resolve } from 'path';

const DIMS = 768;

async function buildIndex(dataPath, vectorsPath, metadataPath, mapFn, label) {
    console.log(`\n[${label}] Cargando datos...`);
    const raw = await readFile(dataPath, 'utf-8');
    const records = JSON.parse(raw);
    console.log(`[${label}] ${records.length} registros cargados.`);

    console.log(`[${label}] Generando ${vectorsPath}...`);
    const buf = new Float32Array(records.length * DIMS);
    for (let i = 0; i < records.length; i++) {
        buf.set(records[i].vector, i * DIMS);
    }
    await writeFile(vectorsPath, Buffer.from(buf.buffer));
    console.log(`[${label}] ${(buf.buffer.byteLength / 1024 / 1024).toFixed(1)} MB`);

    console.log(`[${label}] Generando ${metadataPath}...`);
    const metadata = records.map(mapFn);
    const metaStr = JSON.stringify(metadata);
    await writeFile(metadataPath, metaStr);
    console.log(`[${label}] ${(metaStr.length / 1024 / 1024).toFixed(1)} MB`);
}

async function build() {
    // Escrituras
    await buildIndex(
        resolve('../chunks/scriptures_with_vectors_f16.json'),
        resolve('./vectors.bin'),
        resolve('./metadata.json'),
        r => ({
            id: r.chunk_id,
            text: r.text,
            volume: r.metadata.volume,
            book: r.metadata.book,
            chapter: r.metadata.chapter,
            verses: r.metadata.verses,
        }),
        'Escrituras'
    );

    // Manual General
    await buildIndex(
        resolve('./chunks/manual_with_vectors_f16.json'),
        resolve('./manual_vectors.bin'),
        resolve('./manual_metadata.json'),
        r => ({
            id: r.chunk_id,
            text: r.text,
            chapter_title: r.metadata.chapter_title,
            chapter_slug: r.metadata.chapter_slug,
            section_number: r.metadata.section_number,
            section_title: r.metadata.section_title,
        }),
        'Manual General'
    );

    console.log('\nListo.');
}

build().catch(console.error);
