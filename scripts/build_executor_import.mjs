import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const outputDir = process.argv[2];
const data = JSON.parse(await fs.readFile(path.join(outputDir, 'prepared.json'), 'utf8'));
const wb = Workbook.create();
const sheet = wb.worksheets.add('Для импорта');
const matrix = [data.headers, ...data.rows];
const range = sheet.getRange(`A1:Q${matrix.length}`);
range.values = matrix;
range.format.font = { name: 'Arial', size: 11 };
range.format.rowHeight = 30;
range.format.verticalAlignment = 'top';
sheet.getRange(`A1:Q${matrix.length}`).format.columnWidth = 23;
sheet.getRange('A:A').format.columnWidth = 12;
sheet.getRange('D:D').format.columnWidth = 23;
sheet.getRange('E:E').format.columnWidth = 21;
sheet.getRange('F:F').format.columnWidth = 37;
sheet.getRange('J:J').format.columnWidth = 48;
sheet.getRange('N:O').format.columnWidth = 40;
sheet.getRange('Q:Q').format.columnWidth = 90;
sheet.getRange(`J2:Q${matrix.length}`).format.wrapText = true;
sheet.getRange('A1:Q1').format = {
  fill: '#263B50', font: { name: 'Arial', size: 11, bold: true, color: '#FFFFFF' },
  wrapText: true, rowHeight: 44,
};
sheet.getRange(`L2:M${matrix.length}`).setNumberFormat('0');
sheet.getRange(`E2:E${matrix.length}`).setNumberFormat('@');
for (let i = 0; i < data.rows.length; i++) {
  const r = data.rows[i];
  const lines = Math.max(...[r[9], r[13], r[16]].map(v => String(v || '').split('\n').reduce((n, line) => n + Math.max(1, Math.ceil(line.length / 78)), 0)));
  sheet.getRange(`A${i + 2}:Q${i + 2}`).format.rowHeight = Math.max(30, lines * 15 + 8);
}
sheet.tables.add(`A1:Q${matrix.length}`, true, 'ExecutorsImport');
sheet.freezePanes.freezeRows(1);
console.log((await wb.inspect({kind: 'table', range: 'Для импорта!A1:I4', include: 'values', tableMaxRows: 4, tableMaxCols: 9})).ndjson);
console.log((await wb.inspect({kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!', options: { useRegex: true, maxResults: 20 }})).ndjson);
const preview = await wb.render({sheetName: 'Для импорта', range: 'A1:F5', scale: 1.5});
await fs.writeFile(path.join(outputDir, 'preview.png'), new Uint8Array(await preview.arrayBuffer()));
const preview2 = await wb.render({sheetName: 'Для импорта', range: 'L1:Q5', scale: 1});
await fs.writeFile(path.join(outputDir, 'preview-comments.png'), new Uint8Array(await preview2.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(outputDir, 'Исполнители_для_импорта.xlsx'));
// Serialize the same authored values as UTF-8 CSV for the Django import command.
const values = range.values;
const quote = v => '"' + String(v ?? '').replaceAll('"', '""') + '"';
const csv = '\uFEFF' + values.map(row => row.map(quote).join(';')).join('\r\n') + '\r\n';
await fs.writeFile(path.join(outputDir, 'Исполнители_для_импорта.csv'), csv, 'utf8');
console.log(JSON.stringify({rows: values.length - 1, columns: values[0].length}));
