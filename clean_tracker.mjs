import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const path='D:/专升本学习/outputs/四川专升本_9-10月可编辑计划_官方要求版.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const b=wb.worksheets.getItem('变动补做');
// Restore genuinely blank input cells; the previous export had literal text "37".
b.getRange('A4:G23').values=Array.from({length:20},()=>['','','','','','','']);
b.getRange('H4:H23').values=Array.from({length:20},()=>['未安排']);
const r=wb.worksheets.getItem('周复盘');
r.getRange('C4:D12').values=Array.from({length:9},()=>['','']);
r.getRange('F4:J12').values=Array.from({length:9},()=>['','','','','']);
r.getRange('E4').formulas=[['=IF(OR(C4="",D4=""),"",IFERROR(D4/C4,0))']]; r.getRange('E4:E12').fillDown(); r.getRange('E4:E12').format.numberFormat='0%';
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
console.log('cleaned');
