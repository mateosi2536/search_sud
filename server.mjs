import express from 'express';
import compression from 'compression';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = 3000;

app.use(compression());

app.use(express.static(__dirname));

app.listen(PORT, () => {
    console.log(`\n🚀 Servidor de prueba listo en: http://localhost:${PORT}`);
    console.log(`📡 GZIP está habilitado. El índice de Orama se descargará comprimido.`);
});
