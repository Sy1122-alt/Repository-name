import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const path='D:/专升本学习/计划表/四川专升本_9-10月可编辑计划_官方要求版.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const intro=wb.worksheets.getItem('使用说明');
intro.getRange('A19:B20').values=[
 ['执行调整（9/9起）','学习前安排AI任务；学习开始后不再查看或追加AI任务，结束后再处理。每日记录实际分钟，避免只凭感觉估计。'],
 ['当前反馈结论','第1周实际学习量超过每天120分钟；高数按章节路线推进；英语约每天30词但缺少系统训练；计算机推进偏慢。']
];
intro.getRange('A19:A20').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
intro.getRange('B19:B20').format={fill:'#FFF2CC',font:{color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
const d=wb.worksheets.getItem('每日打卡');
const vals=d.getRange('A4:J400').values;
const start=46273;
for(const row of vals){ if(typeof row[0]!=='number'||row[0]<start) continue; const wd=row[1], t=row[2];
  if(row[5]==='英语'){ if(t==='07:30-08:15') row[4]='英语词汇（30词）+四级阅读1段'; else if(t==='12:30-13:00') row[4]='英语词汇复习（错词+搭配）'; else if(t==='10:00-10:45') row[4]='英语阅读1篇：细节/主旨题'; }
  if(row[5]==='计算机'){ if(t==='12:30-13:00') row[4]='计算机基础：网课1小节+5题自测'; else if(t==='17:30-18:15') row[4]='计算机网课1小节+整理3条要点'; else if(t==='14:30-15:15') row[4]='计算机：按模块完成10题/1个Office小操作'; }
  if(row[5]==='高数'){ if(wd==='周五'&&t==='17:30-18:15') row[4]='高数本周考点小测（10题）+错题1题重做'; else if(wd==='周日'&&t==='09:30-10:15') row[4]='高数章节复盘：整理公式+错题原因'; }
  if(row[5]==='复盘') row[4]='填写实际分钟、完成率、阻碍；安排下周AI任务';
}
d.getRange('A4:J400').values=vals;
const review=wb.worksheets.getItem('周复盘');
review.getRange('C5:J5').values=[['>=120分钟/天','待补填','待计算','高数按章节路线推进；记录每章正确率','词汇约30词/天；从9/9起增加阅读与翻译','计算机推进偏慢；改为小节+5题自测','AI任务打断学习；学习前安排，学习中不查看','先稳定英语专项与计算机小输出，再逐步加量']];
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path);
console.log('updated from 2026-09-09');
