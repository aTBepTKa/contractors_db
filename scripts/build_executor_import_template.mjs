import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const output = process.argv[2];
const wb = Workbook.create();
const data = wb.worksheets.add('Для импорта');
const guide = wb.worksheets.add('Инструкция');
const refs = wb.worksheets.add('Справочники');
const headers = [
  '№ исходной записи', 'Фамилия', 'Имя', 'Отчество', 'Телефон', 'Почта',
  'Тип занятости', 'Статус', 'Источник контакта', 'Комментарий к источнику',
  'Город / местоположение', 'Начал работать с', 'Год рождения', 'ПО',
  'Комментарий по ПО', 'Специальности', 'Общий комментарий',
];
const sources = ['HH.ru', 'Другое', 'Рекомендация', 'Существующий'];
const employment = ['Другое', 'ИП', 'Самозанятый'];
const statuses = ['Активный', 'Космонавт', 'Неактивный', 'Черный список'];
const software = ['3ds Max','Audytor','Audytor CO','Audytor OZC','AutoCAD','AutoCAD Plant 3D','AVEVA PDMS','Civil 3D','Danfoss С.О.','DCAD','KAN CO','MagiCAD','Model Studio CS','nanoCAD','Navisworks','Oventrop','Refprop','Rehau Rauwin','Renga','Revit','SANEXT SET','SketchUp','Solibri','SOLIDWORKS','SPDS','Valtec','V-Ray','АРС-ПС','Гранд-смета','КВМ-дым','КВМ-Лаб','КОМПАС-3D'];
const specialties = [['АиД','Автоматизация и диспетчерезация'],['АПС','Автоматическая пожарная сигнализация'],['АР','Архитектурные решения'],['АУПТ','Автоматическая установка пожаротушения'],['ВК','Водоснабжение и канализация'],['ГП','Генеральный план'],['ИТП','Индивидуальный тепловой пункт'],['КР','Конструктивные решения'],['НВК','Наружные сети водоснабжения и канализации'],['ОВ','Отопление, вентиляция и кондиционирование'],['ООС','Охрана окружающей среды'],['ПБ','Пожарная безопасность'],['ПОС','Проект организации строительства'],['ПТО','Системы пожаротушения и огнезащита'],['СМ','Сметная документация'],['СОУЭ','Система оповещения и управления эвакуацией'],['СС','Сети связи'],['ТМ','Тепломеханические решения'],['ТС','Тепломеханические решения тепловых сетей'],['ТХ','Технологические решения'],['ЭОМ','Электрооборудование и электроосвещение']];

data.getRange('A1:Q201').values = [headers, ...Array.from({length: 200}, () => Array(17).fill(''))];
data.getRange('A1:Q201').format.font = {name: 'Arial', size: 10};
data.getRange('A1:Q1').format = {fill: '#263B50', font: {name:'Arial', size:10, bold:true, color:'#FFFFFF'}, wrapText:true, rowHeight:45, horizontalAlignment:'center', verticalAlignment:'center'};
data.getRange('A2:Q201').format.verticalAlignment = 'top';
data.getRange('A2:Q201').format.rowHeight = 27;
data.getRange('A2:Q201').format.fill = '#FFF9E8';
data.getRange('A:A').format.columnWidth = 13;
data.getRange('B:D').format.columnWidth = 18;
data.getRange('E:E').format.columnWidth = 18;
data.getRange('F:F').format.columnWidth = 30;
data.getRange('G:I').format.columnWidth = 18;
data.getRange('J:J').format.columnWidth = 36;
data.getRange('K:K').format.columnWidth = 24;
data.getRange('L:M').format.columnWidth = 17;
data.getRange('N:N').format.columnWidth = 36;
data.getRange('O:Q').format.columnWidth = 42;
data.getRange('E2:F201').format.numberFormat = '@';
data.getRange('J2:Q201').format.wrapText = true;
data.getRange('G2:G201').dataValidation = {rule:{type:'list', values:employment}};
data.getRange('H2:H201').dataValidation = {rule:{type:'list', values:statuses}};
data.getRange('I2:I201').dataValidation = {rule:{type:'list', values:sources}};
data.getRange('L2:M201').dataValidation = {rule:{type:'whole', operator:'between', formula1:1900, formula2:2100}};
data.tables.add('A1:Q201', true, 'ExecutorImportTable');
data.freezePanes.freezeRows(1);
data.freezePanes.freezeColumns(3);
data.showGridLines = false;
data.tabColor = '#263B50';

guide.getRange('A1:F1').merge(); guide.getRange('A1').values = [['Шаблон импорта исполнителей']];
guide.getRange('A1:F1').format = {font:{name:'Arial', size:15, bold:true, color:'#263B50'}, rowHeight:30};
const guideRows = [
  ['Как заполнить', 'Заполняйте строки на листе «Для импорта». Не переименовывайте лист и заголовки столбцов. Пустые строки игнорируются.'],
  ['Обязательные поля', '№ исходной записи, Фамилия, Имя, Статус. Номер должен быть уникальным внутри файла.'],
  ['Телефон', 'Текст в формате +79991234567. Если телефон скрыт или неизвестен, оставьте ячейку пустой.'],
  ['Тип занятости', 'Выберите из списка. Если оставить пустым, импорт использует «Самозанятый».'],
  ['ПО', 'Несколько программ указывайте через точку с запятой, например: Revit; AutoCAD. Используйте значения со справочного листа.'],
  ['Специальности', 'Указывайте коды через точку с запятой, например: ОВ; ВК; НВК. Расшифровки есть на листе «Справочники».'],
  ['Годы', 'В полях «Начал работать с» и «Год рождения» указывайте только четырёхзначный год.'],
  ['Комментарии', 'Дополнительные контакты и опыт по типам объектов указывайте в «Общем комментарии».'],
  ['Импорт', 'Сохраните файл в формате XLSX. Система проверит все строки до записи и не перезапишет совпадающих исполнителей.'],
];
guide.getRange(`A3:B${guideRows.length+2}`).values = guideRows;
guide.getRange('A3:A11').format = {fill:'#DDEBF7', font:{name:'Arial', size:10, bold:true, color:'#263B50'}, verticalAlignment:'top'};
guide.getRange('B3:B11').format = {font:{name:'Arial', size:10}, wrapText:true, verticalAlignment:'top'};
guide.getRange('A3:B11').format.borders = {preset:'all', style:'thin', color:'#D9E1E8'};
guide.getRange('A:A').format.columnWidth = 23; guide.getRange('B:B').format.columnWidth = 100;
guide.getRange('A3:B11').format.autofitRows(); guide.showGridLines = false; guide.tabColor = '#7F8C8D';

refs.getRange('A1:E1').values = [['Источники контакта','Типы занятости','Статусы','ПО','Код специальности']];
refs.getRange('F1').values = [['Наименование специальности']];
const maxRows = Math.max(sources.length, employment.length, statuses.length, software.length, specialties.length);
const refRows = Array.from({length:maxRows}, (_,i) => [sources[i]||'', employment[i]||'', statuses[i]||'', software[i]||'', specialties[i]?.[0]||'', specialties[i]?.[1]||'']);
refs.getRange(`A2:F${maxRows+1}`).values = refRows;
refs.getRange(`A1:F${maxRows+1}`).format.font = {name:'Arial', size:10};
refs.getRange('A1:F1').format = {fill:'#596B7D', font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'}, wrapText:true, horizontalAlignment:'center'};
refs.getRange('A:D').format.columnWidth = 26; refs.getRange('E:E').format.columnWidth = 18; refs.getRange('F:F').format.columnWidth = 48;
refs.freezePanes.freezeRows(1); refs.showGridLines = false; refs.tabColor = '#A6A6A6';

wb.recalculate();
console.log((await wb.inspect({kind:'table', range:'Для импорта!A1:Q3', include:'values,formulas', tableMaxRows:3, tableMaxCols:17})).ndjson);
console.log((await wb.inspect({kind:'match', searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options:{useRegex:true,maxResults:50}})).ndjson);
const preview = await wb.render({sheetName:'Для импорта', range:'A1:I8', scale:1.2});
await fs.writeFile(output.replace(/\.xlsx$/, '.png'), new Uint8Array(await preview.arrayBuffer()));
await (await SpreadsheetFile.exportXlsx(wb)).save(output);
