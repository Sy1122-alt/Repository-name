import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const path='D:/专升本学习/计划表/四川专升本_9-10月可编辑计划_官方要求版.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const intro=wb.worksheets.getItem('使用说明');
intro.getRange('A18:B18').values=[['宿舍门禁','22:30关门；所有晚间安排须在22:20前结束并返回宿舍，22:20后不安排外出或实验室任务']];
intro.getRange('A18:A18').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
intro.getRange('B18:B18').format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
const d=wb.worksheets.getItem('每日打卡');
const vals=d.getRange('A4:J400').values; let count=0;
for(const row of vals){
 if(row[2]==='21:50-22:35'){ row[2]='21:50-22:15'; row[4]='计算机练习（25分钟，22:20前返宿）'; row[6]=25; row[9]='宿舍22:30关门，需预留返宿时间'; count++; }
}
d.getRange('A4:J400').values=vals;
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
console.log('updated rows',count);
