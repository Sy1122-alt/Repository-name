import fs from 'node:fs/promises';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const outDir = 'D:/专升本学习/outputs';
await fs.mkdir(outDir, { recursive: true });
const navy = '#1F4E78', blue = '#D9EAF7', light = '#F5F8FB', green = '#E2F0D9', orange = '#FCE4D6', gray = '#667085';
function styleTitle(s, range) { s.getRange(range).format = { fill: navy, font: { bold: true, color: '#FFFFFF', size: 14 }, horizontalAlignment: 'center', verticalAlignment: 'center' }; }
function styleHeader(s, range) { s.getRange(range).format = { fill: blue, font: { bold: true, color: '#17365D' }, horizontalAlignment: 'center', verticalAlignment: 'center', wrapText: true, borders: { preset: 'all', style: 'thin', color: '#B7C9D6' } }; }
function styleBody(s, range) { s.getRange(range).format = { fill: '#FFFFFF', font: { color: '#1F2937', size: 10 }, verticalAlignment: 'center', wrapText: true, borders: { preset: 'inside', style: 'thin', color: '#D9E2F3' } }; }
function widths(s, cols) { for (const [c,w] of Object.entries(cols)) s.getRange(`${c}:${c}`).format.columnWidth = w; }

// Workbook 1: editable study plan
const wb = Workbook.create();
const intro = wb.worksheets.add('使用说明');
intro.showGridLines = false;
intro.mergeCells('A1:H1'); intro.getRange('A1').values = [['四川专升本 2026-2027 备考计划（9-10月执行版）']]; styleTitle(intro,'A1:H1'); intro.getRange('A1:H1').format.rowHeight = 28;
intro.getRange('A3:B12').values = [
 ['目标','2027-04-16考试；目标总分约400；优先高数、英语，计算机快速提分'],
 ['执行测试','9/1-9/14为两周测量期：按表完成并记录实际分钟数，不追求满负荷'],
 ['核心保底','当天至少：英语单词20分钟 + 高数基础题30分钟 + 计算机基础20分钟'],
 ['时间原则','单次学习45分钟，休息10分钟；睡眠优先，逐步将入睡时间提前'],
 ['变动处理','临时有课/身体不适时，先完成核心保底；未完成任务移入“变动补做”'],
 ['运动原则','膝盖不适时取消跳绳和跑步，改为快走、上肢和核心；运动以不加重疼痛为准'],
 ['周复盘','每周日记录实际学习时长、完成率、最常见阻碍，并调整下周目标'],
 ['资料策略','先用已有上一届资料与网课；9月完成范围确认和资料筛选，不盲目购买'],
 ['输入区域','每日打卡中的“实际分钟”“状态”“变动原因”是主要编辑区域'],
 ['附件课表','固定课表依据用户提供的课表PDF；调课时只改固定课表，不改任务模板']
 ]; styleHeader(intro,'A3:A12'); styleBody(intro,'B3:B12'); widths(intro,{A:16,B:105}); intro.getRange('A3:B12').format.rowHeight = 34;

const fixed = wb.worksheets.add('固定课表'); fixed.showGridLines=false;
fixed.mergeCells('A1:H1'); fixed.getRange('A1').values=[['固定课表与可用学习窗口（可直接修改）']]; styleTitle(fixed,'A1:H1');
fixed.getRange('A3:H3').values=[['星期','1-2节 09:00-10:30','3-4节 10:45-12:15','午间','5-6节 14:00-15:30','7-8节 15:45-17:15','9-10节 18:30-20:00','备注']]; styleHeader(fixed,'A3:H3');
fixed.getRange('A4:H10').values=[
 ['周一','空','空','12:15-14:00','空','生产管理','空','课程以课表为准'],
 ['周二','智能制造基础','空','12:15-14:00','空','空','空',''],
 ['周三','3D打印技术与应用','空','12:15-14:00','空','生产管理','形势与政策V',''],
 ['周四','空','电机与电气控制技术','12:15-14:00','空','空','智能设计与CAE分析',''],
 ['周五','3D打印技术与应用','空','12:15-14:00','空','电机与电气控制技术','空',''],
 ['周六','空','空','12:15-14:00','空','空','空',''],
 ['周日','空','空','12:15-14:00','空','空','空','第13-14周另有创新项目综合实习，具体时段待通知']
 ]; styleBody(fixed,'A4:H10'); widths(fixed,{A:10,B:22,C:24,D:16,E:16,F:22,G:24,H:45}); fixed.freezePanes.freezeRows(3);

const plan = wb.worksheets.add('阶段与周计划'); plan.showGridLines=false;
plan.mergeCells('A1:G1'); plan.getRange('A1').values=[['9-10月阶段目标与每周任务']]; styleTitle(plan,'A1:G1');
plan.getRange('A3:G3').values=[['阶段','日期','高数','英语','计算机','专业课/实验室','周复盘标准']]; styleHeader(plan,'A3:G3');
plan.getRange('A4:G11').values=[
 ['执行测试','9/1-9/14','复习函数、极限、导数基础；每天30-45分钟','四级高频词/基础词每天20分钟；每周2次阅读','计算机基础概念、Windows/网络入门，每天20分钟','每周2次，每次45分钟','完成率>=70%；统计真实学习时长与阻碍'],
 ['基础建立','9/15-9/30','一元函数微分与积分基础；每周1次小测','词汇持续；每周3篇阅读；每周1次翻译/作文训练','Office/计算机基础操作；每周1套章节练习','每周2次','总学习时长较测试期提升10%-20%'],
 ['基础建立','10/1-10/15','积分、微分应用与典型题；错题归档','词汇+长难句；每周4篇阅读；听力入门跟读','数据结构/程序设计基础入门','每周2次','高数小测正确率逐步达到60%'],
 ['强化过渡','10/16-10/31','综合题与章节串联；每周1次限时训练','阅读速度、翻译、作文模板；每周1次小套题','重点章节刷题与错题回炉','每周2次','按时完成率>=75%，形成可复用错题本'],
 ['每周固定','周一至周五','5个45分钟单元/周起步，按每日表执行','每天20-30分钟','每天20分钟起步','2次45分钟','周日填写复盘'],
 ['周末安排','周六','2-3个学习单元+运动','1个英语单元','1个计算机单元','可选1次','保留约2小时娱乐'],
 ['周末安排','周日','2个学习单元+周测/复盘','听力或作文轮换','错题回顾','整理实验室任务','娱乐不少于1小时，完成下周调整'],
 ['假期最低标准','节假日/临时忙碌日','30分钟基础题','20分钟单词','20分钟基础课','有余力再做','三科保底完成即可']
 ]; styleBody(plan,'A4:G11'); widths(plan,{A:16,B:18,C:38,D:38,E:34,F:24,G:38}); plan.getRange('A4:G11').format.rowHeight=44;

const daily = wb.worksheets.add('每日打卡'); daily.showGridLines=false;
daily.mergeCells('A1:J1'); daily.getRange('A1').values=[['每日时间表与执行记录（9/1-10/31）']]; styleTitle(daily,'A1:J1');
daily.getRange('A3:J3').values=[['日期','星期','时间段','固定安排','具体任务','科目','计划分钟','实际分钟','状态','变动原因/备注']]; styleHeader(daily,'A3:J3');
const rows=[]; const start=new Date(2026,8,1); const end=new Date(2026,9,31); const names=['周日','周一','周二','周三','周四','周五','周六'];
const tasks={
 '周一':[['06:50-07:15','运动','晨间快走/低冲击操','运动',25],['07:30-08:15','空','高数基础题+订正','高数',45],['12:30-13:00','空','英语单词','英语',30],['19:50-20:35','空','计算机网课/笔记','计算机',45],['21:00-21:25','空','拉伸与当天复盘','运动',25]],
 '周二':[['06:50-07:15','运动','晨间快走/力量基础','运动',25],['07:30-08:15','空','英语单词+短阅读','英语',45],['12:30-13:00','空','计算机基础概念','计算机',30],['18:30-20:00','智能制造基础','上课','课程',0],['20:30-21:15','空','高数基础题','高数',45]],
 '周三':[['06:50-07:15','运动','低冲击操/快走','运动',25],['12:30-13:00','空','英语单词','英语',30],['17:30-18:15','空','计算机网课','计算机',45],['20:30-21:15','空','高数复习与错题','高数',45]],
 '周四':[['06:50-07:15','运动','快走或上肢训练','运动',25],['07:30-08:15','空','高数基础题','高数',45],['12:30-13:00','空','英语单词','英语',30],['20:15-21:00','空','计算机练习','计算机',45]],
 '周五':[['06:50-07:15','运动','低冲击操/拉伸','运动',25],['12:30-13:00','空','英语单词+阅读','英语',30],['17:30-18:15','空','高数小测','高数',45],['20:30-21:15','空','专业课/实验室任务','专业课',45]],
 '周六':[['08:00-08:30','运动','快走（膝盖友好）','运动',30],['09:00-09:45','空','高数专题','高数',45],['10:00-10:45','空','英语阅读/翻译','英语',45],['14:30-15:15','空','计算机网课','计算机',45],['20:00-22:00','娱乐','手机/游戏/朋友','娱乐',0]],
 '周日':[['08:30-09:00','运动','恢复性快走+拉伸','运动',30],['09:30-10:15','空','本周错题整理','高数',45],['10:30-11:15','空','英语听力跟读/作文轮换','英语',45],['14:30-15:15','空','计算机错题回顾','计算机',45],['16:00-16:30','复盘','填写周复盘并安排下周','复盘',30],['20:00-21:00','娱乐','自由娱乐','娱乐',0]]};
for(let d=new Date(start); d<=end; d.setDate(d.getDate()+1)){ const wd=names[d.getDay()]; for(const t of tasks[wd]) rows.push([new Date(d),wd,...t,'','未开始','']); }
daily.getRange(`A4:J${rows.length+3}`).values=rows; styleBody(daily,`A4:J${rows.length+3}`); daily.getRange(`A4:A${rows.length+3}`).format.numberFormat='yyyy-mm-dd'; daily.getRange(`G4:H${rows.length+3}`).format.numberFormat='0'; widths(daily,{A:13,B:8,C:15,D:20,E:34,F:10,G:11,H:11,I:12,J:30}); daily.getRange(`I4:I${rows.length+3}`).dataValidation={rule:{type:'list',values:['未开始','进行中','完成','部分完成','延期','取消']}}; daily.freezePanes.freezeRows(3);
daily.getRange(`I4:I${rows.length+3}`).conditionalFormats.add('containsText',{text:'完成',format:{fill:green}}); daily.getRange(`I4:I${rows.length+3}`).conditionalFormats.add('containsText',{text:'延期',format:{fill:orange}});

const backlog=wb.worksheets.add('变动补做'); backlog.showGridLines=false; backlog.mergeCells('A1:H1'); backlog.getRange('A1').values=[['变动补做区：临时任务先登记，再安排回补']]; styleTitle(backlog,'A1:H1'); backlog.getRange('A3:H3').values=[['登记日期','原计划日期','科目','任务','原计划分钟','原因','回补日期','完成状态']]; styleHeader(backlog,'A3:H3'); backlog.getRange('A4:H23').values=Array.from({length:20},()=>['','','','','','','','未安排']); styleBody(backlog,'A4:H23'); widths(backlog,{A:13,B:13,C:12,D:38,E:14,F:30,G:13,H:14}); backlog.getRange('H4:H23').dataValidation={rule:{type:'list',values:['未安排','已安排','完成','取消']}}; backlog.freezePanes.freezeRows(3);

const review=wb.worksheets.add('周复盘'); review.showGridLines=false; review.mergeCells('A1:J1'); review.getRange('A1').values=[['周复盘：用数据调节下一周，不用意志力硬撑']]; styleTitle(review,'A1:J1'); review.getRange('A3:J3').values=[['周次','日期范围','计划分钟','实际分钟','完成率','高数进度/正确率','英语进度','计算机进度','最大阻碍','下周调整']]; styleHeader(review,'A3:J3');
const rev=[]; for(let i=0;i<9;i++){ const s=new Date(2026,8,1+i*7), e=new Date(s); e.setDate(e.getDate()+6); rev.push([`第${i+1}周`,`${s.getMonth()+1}/${s.getDate()}-${e.getMonth()+1}/${e.getDate()}`,'','','','','','','','']); } review.getRange('A4:J12').values=rev; styleBody(review,'A4:J12'); widths(review,{A:10,B:16,C:13,D:13,E:12,F:24,G:24,H:24,I:28,J:34}); review.getRange('E4').formulas=[['=IFERROR(D4/C4,0)']]; review.getRange('E4:E12').fillDown(); review.getRange('E4:E12').format.numberFormat='0%'; review.freezePanes.freezeRows(3);

const xlsx=await SpreadsheetFile.exportXlsx(wb); await xlsx.save(`${outDir}/四川专升本_9-10月可编辑计划.xlsx`);

// Workbook 2: subject scope and resource register
const swb=Workbook.create(); const s=swb.worksheets.add('考试范围总览'); s.showGridLines=false; s.mergeCells('A1:H1'); s.getRange('A1').values=[['四川统招专升本（三科）范围与资料整理（待官方大纲核对版）']]; styleTitle(s,'A1:H1'); s.getRange('A3:H3').values=[['科目','当前基础','9-10月重点','11-12月方向','1-3月方向','已有资料/资源','缺口与动作','核对来源']]; styleHeader(s,'A3:H3'); s.getRange('A4:H6').values=[
 ['高数','有基础但久未接触','函数、极限、导数、积分基础；章节题与错题','综合题、真题、限时训练','套题、押重点、错题回炉','宋浩《四川省专升本指导丛书》、上一届资料','确认报考专业对应数学类别和最新考试大纲；补齐真题','四川省教育考试院/四川省教育厅最新通知'],
 ['英语','四级380；阅读尚可，词汇/听力/作文翻译弱','词汇、阅读、长难句、听力跟读；翻译作文基础','真题精练、听力、翻译与作文成稿','套题计时、作文模板和查漏补缺','上一届资料；暂未购资料','整理词表与错题本；确认四川专升本英语题型和词表','四川省教育考试院最新考试说明'],
 ['计算机','零基础但预计提分快','计算机基础、Windows/网络、Office；跟网课做章节题','数据结构/程序设计等大纲模块；真题','套题、错题、常见操作题','网课资源、上一届资料','确认考试是否包含操作题、程序设计及具体软件版本','四川省教育考试院最新考试说明']
 ]; styleBody(s,'A4:H6'); widths(s,{A:12,B:24,C:38,D:38,E:38,F:34,G:42,H:34}); s.getRange('A4:H6').format.rowHeight=62;
const r=swb.worksheets.add('资料清单'); r.showGridLines=false; r.mergeCells('A1:G1'); r.getRange('A1').values=[['资料清单与使用顺序']]; styleTitle(r,'A1:G1'); r.getRange('A3:G3').values=[['科目','资料/来源','用途','开始使用','每周产出','状态','备注']]; styleHeader(r,'A3:G3'); r.getRange('A4:G11').values=[
 ['高数','宋浩四川专升本指导丛书','主教材与章节练习','9/1','1章笔记+错题','待开始','先按大纲筛章节'],['高数','上一届资料','补充题型、真题','基础完成后','1套章节题','待开始','核对是否过时'],['英语','上一届资料','阅读、翻译、作文参考','9/1','3篇阅读+1次翻译/作文','待开始','词汇先于刷题'],['英语','自建词汇表','每天复习与滚动复现','9/1','每周新增/复习记录','待开始','按错词优先'],['计算机','网课资源','建立知识框架','9/1','3-5节课笔记','待开始','看完立刻做题'],['计算机','上一届资料','章节题与错题','对应章节后','1次章节练习','待开始','先确认软件版本'],['三科','四川最新考试大纲/通知','确认范围和题型','尽快','完成一次范围核对','未核对','以官方发布为准'],['三科','错题本/错题表','记录错误原因与再练日期','9/1','每周回炉一次','待开始','不要只抄答案'] ]; styleBody(r,'A4:G11'); widths(r,{A:12,B:28,C:34,D:14,E:26,F:14,G:36}); r.getRange('F4:F11').dataValidation={rule:{type:'list',values:['未开始','进行中','已完成','需更新']}};
const note=swb.worksheets.add('核对记录'); note.showGridLines=false; note.mergeCells('A1:E1'); note.getRange('A1').values=[['官方范围核对记录（填写后替换“待核对”）']]; styleTitle(note,'A1:E1'); note.getRange('A3:E3').values=[['科目','官方文件名称','发布日期','已核对内容','链接/文件位置']]; styleHeader(note,'A3:E3'); note.getRange('A4:E6').values=[['高数','待核对','','考试范围、分值、题型',''],['英语','待核对','','词表、题型、分值',''],['计算机','待核对','','模块、题型、软件版本','']]; styleBody(note,'A4:E6'); widths(note,{A:12,B:30,C:16,D:44,E:48});
const sx=await SpreadsheetFile.exportXlsx(swb); await sx.save(`${outDir}/四川专升本_三科范围与资料清单.xlsx`);

// Render previews for QA
for (const [book,sheet,file] of [[wb,'每日打卡','preview_daily.png'],[wb,'阶段与周计划','preview_plan.png'],[swb,'考试范围总览','preview_scope.png']]) { const p=await book.render({sheetName:sheet,autoCrop:'all',scale:1,format:'png'}); await fs.writeFile(`${outDir}/${file}`,new Uint8Array(await p.arrayBuffer())); }
console.log('created', outDir);
