import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const path='D:/专升本学习/outputs/四川专升本_9-10月可编辑计划.xlsx';
const input=await FileBlob.load(path); const wb=await SpreadsheetFile.importXlsx(input);
const s=wb.worksheets.getItem('固定课表');
// Replace the fixed-course grid with the corrected 9-12 evening blocks.
s.getRange('A3:I10').values=[
 ['星期','1-2节 09:00-10:30','3-4节 10:45-12:15','午间','5-6节 14:00-15:30','7-8节 15:45-17:15','9-10节 18:30-20:00','11-12节 20:10-21:40','备注'],
 ['周一','空','空','12:15-14:00','空','生产管理','空','空','第7-8节课程'],
 ['周二','智能制造基础','空','12:15-14:00','空','空','空','空','第1-2节课程'],
 ['周三','3D打印技术与应用','空','12:15-14:00','空','生产管理','形势与政策V','空','第1-2、7-8、9-10节课程'],
 ['周四','空','电机与电气控制技术','12:15-14:00','空','空','智能设计与CAE分析','智能设计与CAE分析','实际为第9-12节连续课程'],
 ['周五','3D打印技术与应用','空','12:15-14:00','空','电机与电气控制技术','空','空','第1-2、7-8节课程'],
 ['周六','空','空','12:15-14:00','空','空','空','空',''],
 ['周日','空','空','12:15-14:00','空','空','空','空','第13-14周另有创新项目综合实习，具体时段待通知']
];
s.getRange('A3:I3').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
s.getRange('A4:I10').format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},verticalAlignment:'center',wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
for (const [c,w] of Object.entries({A:10,B:22,C:24,D:16,E:16,F:22,G:24,H:24,I:42})) s.getRange(`${c}:${c}`).format.columnWidth=w;
const d=wb.worksheets.getItem('每日打卡');
// Thursday evening study moves after the 9-12 class block.
const vals=d.getRange('A4:J289').values;
for(const row of vals){ if(row[1]==='周四' && row[2]==='20:15-21:00'){ row[2]='21:50-22:35'; row[3]='课后'; row[4]='计算机练习'; row[5]='计算机'; row[6]=45; row[7]=''; row[8]='未开始'; row[9]='周四课程延续至第11-12节，任务顺延'; } }
d.getRange('A4:J289').values=vals;
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
const preview=await wb.render({sheetName:'固定课表',autoCrop:'all',scale:1,format:'png'}); await fs.writeFile('D:/专升本学习/outputs/preview_fixed_updated.png',new Uint8Array(await preview.arrayBuffer()));
console.log('updated');
