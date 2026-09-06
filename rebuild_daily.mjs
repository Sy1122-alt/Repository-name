import fs from 'node:fs/promises';
import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const path='D:/专升本学习/outputs/四川专升本_9-10月可编辑计划_修正版.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const s=wb.worksheets.getItem('每日打卡');
const names=['周日','周一','周二','周三','周四','周五','周六'];
const schedules={
 '周一':[['06:50-07:15','运动','晨间快走/低冲击操','运动',25],['07:30-08:15','空','高数基础题+订正','高数',45],['09:00-10:30','生产管理（第7-8节）','上课','课程',0],['12:30-13:00','空','英语单词','英语',30],['19:50-20:35','空','计算机网课/笔记','计算机',45],['21:00-21:25','空','拉伸与当天复盘','运动',25]],
 '周二':[['06:50-07:15','运动','晨间快走/力量基础','运动',25],['07:30-08:15','空','英语单词+短阅读','英语',45],['09:00-10:30','智能制造基础（第1-2节）','上课','课程',0],['12:30-13:00','空','计算机基础概念','计算机',30],['20:30-21:15','空','高数基础题','高数',45]],
 '周三':[['06:50-07:15','运动','低冲击操/快走','运动',25],['09:00-10:30','3D打印技术与应用（第1-2节）','上课','课程',0],['12:30-13:00','空','英语单词','英语',30],['15:45-17:15','生产管理（第7-8节）','上课','课程',0],['17:30-18:15','空','计算机网课','计算机',45],['18:30-20:00','形势与政策V（第9-10节）','上课','课程',0],['20:30-21:15','空','高数复习与错题','高数',45]],
 '周四':[['06:50-07:15','运动','快走或上肢训练','运动',25],['07:30-08:15','空','高数基础题','高数',45],['10:45-12:15','电机与电气控制技术（第3-4节）','上课','课程',0],['12:30-13:00','空','英语单词','英语',30],['18:30-21:40','智能设计与CAE分析（第9-12节）','上课','课程',0],['21:50-22:35','课后','计算机练习','计算机',45]],
 '周五':[['06:50-07:15','运动','低冲击操/拉伸','运动',25],['09:00-10:30','3D打印技术与应用（第1-2节）','上课','课程',0],['12:30-13:00','空','英语单词+阅读','英语',30],['15:45-17:15','电机与电气控制技术（第7-8节）','上课','课程',0],['17:30-18:15','空','高数小测','高数',45],['20:30-21:15','空','专业课/实验室任务','专业课',45]],
 '周六':[['08:00-08:30','运动','快走（膝盖友好）','运动',30],['09:00-09:45','空','高数专题','高数',45],['10:00-10:45','空','英语阅读/翻译','英语',45],['14:30-15:15','空','计算机网课','计算机',45],['20:00-22:00','娱乐','手机/游戏/朋友','娱乐',0]],
 '周日':[['08:30-09:00','运动','恢复性快走+拉伸','运动',30],['09:30-10:15','空','本周错题整理','高数',45],['10:30-11:15','空','英语听力跟读/作文轮换','英语',45],['14:30-15:15','空','计算机错题回顾','计算机',45],['16:00-16:30','复盘','填写周复盘并安排下周','复盘',30],['20:00-21:00','娱乐','自由娱乐','娱乐',0]]};
const rows=[]; const start=new Date(2026,8,1), end=new Date(2026,9,31);
function courseInWeek(wd,time,week){
 if(wd==='周一'&&time==='15:45-17:15') return week<=11;
 if(wd==='周二'&&time==='09:00-10:30') return week<=12;
 if(wd==='周三'&&time==='09:00-10:30') return week<=11;
 if(wd==='周三'&&time==='15:45-17:15') return week<=9 && week%2===1;
 if(wd==='周三'&&time==='18:30-20:00') return week>=7&&week<=10;
 if(wd==='周四'&&time==='10:45-12:15') return week<=11;
 if(wd==='周四'&&time==='18:30-21:40') return week<=10;
 if(wd==='周五'&&time==='09:00-10:30') return week>=2&&week<=10&&week%2===0;
 if(wd==='周五'&&time==='15:45-17:15') return week<=9&&week%2===1;
 return true;
}
for(let d=new Date(start);d<=end;d.setDate(d.getDate()+1)){const wd=names[d.getDay()];const week=Math.floor((d-start)/86400000/7)+1;for(const t of schedules[wd]){if(t[3]==='课程'&&!courseInWeek(wd,t[0],week)) continue; rows.push([new Date(d),wd,t[0],t[1],t[2],t[3],t[4],null,'未开始',`第${week}周`]);}}
s.getRange('A3:J400').clear({applyTo:'contents'});
s.getRange('A3:J3').values=[['日期','星期','时间段','固定安排','具体任务','科目','计划分钟','实际分钟','状态','变动原因/备注']];
s.getRange(`A4:J${rows.length+3}`).values=rows;
s.getRange('A3:J3').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
s.getRange(`A4:J${rows.length+3}`).format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},verticalAlignment:'center',wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
s.getRange(`A4:A${rows.length+3}`).format.numberFormat='yyyy-mm-dd';
s.getRange(`I4:I${rows.length+3}`).dataValidation={rule:{type:'list',values:['未开始','进行中','完成','部分完成','延期','取消']}};
s.getRange(`I4:I${rows.length+3}`).conditionalFormats.add('containsText',{text:'完成',format:{fill:'#E2F0D9'}}); s.getRange(`I4:I${rows.length+3}`).conditionalFormats.add('containsText',{text:'延期',format:{fill:'#FCE4D6'}});
for(const [c,w] of Object.entries({A:13,B:8,C:18,D:30,E:34,F:10,G:11,H:11,I:12,J:30})) s.getRange(`${c}:${c}`).format.columnWidth=w;
s.freezePanes.freezeRows(3);
const out=await SpreadsheetFile.exportXlsx(wb); await out.save('D:/专升本学习/outputs/四川专升本_9-10月可编辑计划_修正版_v2.xlsx');
const p=await wb.render({sheetName:'每日打卡',range:'A1:J35',scale:1,format:'png'}); await fs.writeFile('D:/专升本学习/outputs/preview_daily_fixed.png',new Uint8Array(await p.arrayBuffer()));
console.log('daily rebuilt',rows.length);
