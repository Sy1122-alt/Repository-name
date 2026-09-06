import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const dir='D:/专升本学习/outputs';
const planPath=`${dir}/四川专升本_9-10月可编辑计划_官方要求版.xlsx`;
const plan=await SpreadsheetFile.importXlsx(await FileBlob.load(planPath));
const stage=plan.worksheets.getItem('阶段与周计划');
stage.getRange('A4:G11').values=[
 ['执行测试','9/1-9/14','第1章函数/极限/连续：按考点做基础题；每周末小测','词汇、阅读、翻译/写作基础','基础知识与软硬件入门','每周2次，每次45分钟','完成率>=70%；记录真实学习时长'],
 ['基础一','9/15-9/30','第2章一元函数微分学：导数、微分、中值定理、洛必达、极值；每4个高数单元穿插1个线代单元','词汇+阅读；每周1次翻译或100词写作','Windows与Office基础操作','每周2次','高数基础题正确率逐步提高'],
 ['基础二','10/1-10/15','第3章一元函数积分学：不定积分、定积分、面积体积；线代行列式/矩阵','长难句、阅读推断、听力跟读','办公自动化重点：Word/Excel','每周2次','完成第1-3章第一轮'],
 ['基础三','10/16-10/31','第4章向量与空间解析几何；第5章多元函数与二重积分；继续线代矩阵/方程组','阅读速度、翻译、作文模板','网络与信息安全、算法程序设计入门','每周2次','完成率>=75%，错题归档'],
 ['11月衔接','11/1-11/30','第6章无穷级数；第7章常微分方程；补充一阶齐次微分方程；线代向量/方程组','题型轮换与阶段套题','数据库、新技术模块','每周2次','完成全书第一轮并列出缺口'],
 ['12月强化','12/1-12/31','按官方约80%高数、20%线代比例综合训练；重点补缺','真题、听力、翻译、写作','按官方模块比例刷题','每周2次','每周一次限时训练'],
 ['1-3月冲刺','1/1-4/15','套题计时、错题回炉、线代保持20%权重；每周复盘','套题计时，作文不少于100词','综合应用题与错题回炉','按需','模拟考试与查漏补缺'],
 ['补充任务','随第7章学习安排','一阶齐次微分方程不在本书目录中：使用网课/上一届资料补学，至少完成概念、通解方法和基础题','', '', '', '补学完成后在资料清单标记']
];
const route=plan.worksheets.getOrAdd('高数章节路线'); route.showGridLines=false;
route.mergeCells('A1:G1'); route.getRange('A1').values=[['高数章节路线与官方考纲核对']]; route.getRange('A1:G1').format={fill:'#1F4E78',font:{bold:true,color:'#FFFFFF',size:14},horizontalAlignment:'center'};
route.getRange('A3:G3').values=[['顺序','书中章节','官方对应范围','安排建议','必须掌握/核对','缺口处理','状态']]; route.getRange('A3:G3').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
route.getRange('A4:G11').values=[
 [1,'第1章 函数、极限与连续','函数、极限、连续','9/1-9/7','定义域、极限、连续性、间断点','按书中考点学习','未开始'],
 [2,'第2章 一元函数微分学','导数、微分、中值定理及应用','9/8-9/21','求导、洛必达、极值、单调性、凹凸性','按书中考点学习','未开始'],
 [3,'第3章 一元函数积分学','不定积分、定积分及应用','9/22-10/5','换元、分部、面积、体积、广义积分','按书中考点学习','未开始'],
 [4,'第8章 线性代数（穿插）','行列式、矩阵','从第2章起每4个高数单元插入1个','矩阵运算、逆矩阵、秩、矩阵方程','保持约20%学习量','未开始'],
 [5,'第4章 向量代数与空间解析几何','向量、平面直线、空间曲面','10月上旬','向量积、平面直线方程、曲面识别','核对曲面类型是否齐全','未开始'],
 [6,'第5章 多元函数微分学与二重积分','多元微分、二重积分','10月中下旬','偏导、全微分、极值、直角/极坐标积分','按书中考点学习','未开始'],
 [7,'第6章无穷级数、第7章常微分方程','级数、微分方程','11月','收敛性、幂级数、常微分方程','补充一阶齐次微分方程','未开始'],
 [8,'综合复习','官方高数约80%、线代约20%','12月起','证明题、应用题、限时套题','按错题调整','未开始']
]; route.getRange('A4:G11').format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},verticalAlignment:'center',wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
for(const [c,w] of Object.entries({A:8,B:25,C:32,D:28,E:38,F:32,G:12})) route.getRange(`${c}:${c}`).format.columnWidth=w;
const scopePath=`${dir}/四川专升本_三科范围与资料清单_官方要求版.xlsx`;
const swb=await SpreadsheetFile.importXlsx(await FileBlob.load(scopePath));
const s=swb.worksheets.getItem('考试范围总览');
s.getRange('G4').values=[['150分/120分钟；高数约80%，线代约20%；闭卷笔试']];
s.getRange('G4:G6').format.wrapText=true;
const reg=swb.worksheets.getItem('资料清单');
reg.getRange('A12:G12').values=[['高数','网课/上一届资料：一阶齐次微分方程补充','弥补本书第7章目录未见的官方要求','第7章学习时','概念+通解方法+基础题','未开始','官方要求明确“了解齐次微分方程的解法”']];
reg.getRange('A12:G12').format={fill:'#FFF2CC',font:{color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
const note=swb.worksheets.getItem('核对记录');
note.getRange('A8:E8').values=[['高数缺口记录','第7章一阶齐次微分方程','官方要求有，本书目录暂未见','补充网课/资料后再标记完成','需补学']];
note.getRange('A8:E8').format={fill:'#FFF2CC',font:{color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
const pOut=await SpreadsheetFile.exportXlsx(plan); await pOut.save(planPath);
const sOut=await SpreadsheetFile.exportXlsx(swb); await sOut.save(scopePath);
console.log('optimized in place');
