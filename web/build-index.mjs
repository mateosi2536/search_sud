import { readFile, writeFile } from 'fs/promises';
import { resolve } from 'path';

const DATA_PATH = resolve('../chunks/scriptures_with_vectors_f16.json');
const VECTORS_PATH = resolve('./vectors.bin');
const METADATA_PATH = resolve('./metadata.json');

const DIMS = 768;

async function build() {
    console.log('Cargando datos...');
    const raw = await readFile(DATA_PATH, 'utf-8');
    const records = JSON.parse(raw);
    console.log(`${records.length} registros cargados.`);

    // --- vectors.bin: Float32Array empaquetado ---
    console.log('Generando vectors.bin...');
    const buf = new Float32Array(records.length * DIMS);
    for (let i = 0; i < records.length; i++) {
        buf.set(records[i].vector, i * DIMS);
    }
    await writeFile(VECTORS_PATH, Buffer.from(buf.buffer));
    console.log(`vectors.bin: ${(buf.buffer.byteLength / 1024 / 1024).toFixed(1)} MB`);

    // --- metadata.json: texto + referencias, sin vectores ---
    console.log('Generando metadata.json...');
    const metadata = records.map(r => ({
        id: r.chunk_id,
        text: r.text,
        volume: r.metadata.volume,
        book: r.metadata.book,
        chapter: r.metadata.chapter,
        verses: r.metadata.verses,
    }));
    const metaStr = JSON.stringify(metadata);
    await writeFile(METADATA_PATH, metaStr);
    console.log(`metadata.json: ${(metaStr.length / 1024 / 1024).toFixed(1)} MB`);

    console.log('Listo.');
}

build().catch(console.error);
