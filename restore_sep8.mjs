import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const path='D:/专升本学习/计划表/四川专升本_9-10月可编辑计划_官方要求版.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path)); const d=wb.worksheets.getItem('每日打卡'); const vals=d.getRange('A4:J400').values;
for(const row of vals){ if(row[0]!==46273) continue; if(row[2]==='07:30-08:15') row[4]='英语单词+短阅读'; if(row[2]==='12:30-13:00') row[4]='计算机基础概念'; if(row[2]==='20:30-21:15') row[4]='高数基础题'; }
d.getRange('A4:J400').values=vals; const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path); console.log('restored Sep 8');
