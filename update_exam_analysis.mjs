import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const dir='D:/专升本学习/outputs';
const planPath=`${dir}/四川专升本_9-10月可编辑计划_官方要求版.xlsx`;
const plan=await SpreadsheetFile.importXlsx(await FileBlob.load(planPath));
const stage=plan.worksheets.getItem('阶段与周计划');
stage.getRange('C4:E11').values=[
 ['第1章函数/极限/连续：极限计算、连续求参、间断点；周末做1次小测','词汇启动；20道词汇语法基础题；阅读细节题训练','基础知识、数制转换、软硬件概念'],
 ['第2章微分：导数定义/几何意义、洛必达、中值定理、极值；穿插线代行列式/矩阵','3500词分批；复合从句/非谓语；每周3篇阅读','Windows文件管理+Word样式、多级列表、页面布局'],
 ['第3章积分：微积分互逆性、换元/分部、面积体积；线代矩阵乘法/逆矩阵','完形语境词义；英译汉；应用文格式与100词写作','Excel公式、绝对引用、SUMIF/COUNTIF/AVERAGEIF/VLOOKUP/IF'],
 ['第4章向量空间解析几何；第5章多元与二重积分；重点二重积分计算与极值；继续线代秩/方程组','长难句、主旨/推理题；听力跟读；翻译复合结构','Excel排序筛选分类汇总图表；PowerPoint母版、动画与切换'],
 ['第6章级数；第7章微分方程；补充一阶齐次；综合题：微分方程+级数和函数；矩阵综合','选词填空词形转换、情景对话、完形；每周1套小题','网络安全、算法流程图、查找排序；数据库SQL基础'],
 ['按近年题型做套题：高数22题/150分/120分钟；最后3题练跨章节融合','按近年题型轮换：词法20、阅读16、完形20、对话5、选词10、翻译5、写作1','按模块比例：办公自动化35%优先，软硬件20%，基础15%，其余模块循环'],
 ['模拟训练与错题回炉；保留高数约80%、线代约20%权重','客观题约70%+主观题约30%；作文不少于100词；计时训练','主观题情境化：设计题/综合应用题，强化Office实际操作'],
 ['补充任务：一阶齐次微分方程使用网课/上一届资料补学','', '']
];
const analysis=plan.worksheets.getOrAdd('近年考情参考'); analysis.showGridLines=false;
analysis.mergeCells('A1:H1'); analysis.getRange('A1').values=[['2026真题考情参考（经验资料，不替代官方大纲）']]; analysis.getRange('A1:H1').format={fill:'#1F4E78',font:{bold:true,color:'#FFFFFF',size:14},horizontalAlignment:'center'};
analysis.getRange('A3:H3').values=[['科目','题型/结构','近年重点','主要难点','对你的影响','训练安排','依据文件','可靠性说明']]; analysis.getRange('A3:H3').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
analysis.getRange('A4:H6').values=[
 ['高数','单选10、填空6、计算6，共150分/120分钟','微分21%、多元15%、函数16%、线代18%；综合题涉及微分方程+级数、矩阵综合','极限、导数定义、积分、二重积分、线代运算','高数保持主线；不能只刷基础选择题','每章学完做跨章节小题；12月起整套限时','26四川专升本考情分析-高等数学.pdf.pdf','2026真题分析，属于近年趋势参考'],
 ['英语','词法语法20、阅读16、完形20、对话5、选词10、翻译5、写作1','复合从句、非谓语、语境词义；阅读主旨/推理；应用文书信','词汇搭配、长难句、完形逻辑、词形转换、应用文格式','你的阅读基础可利用；词汇、听力、翻译写作需补短板','每天词汇；每周阅读3篇、翻译1次、写作1次；后期计时','26四川专升本-考情分析-大学英语.pdf.pdf','2026真题分析，题型可能年度调整'],
 ['计算机','单选20、多选10、判断15、填空10、简答3、设计2，共150分/120分钟','办公自动化35%；软硬件20%；基础15%；主观题情境化','Office综合操作、网络安全、流程图、SQL、概念辨析','零基础先抢Office与基础分，再补算法/数据库','9-10月Office实操；11月算法网络；12月综合应用','26四川专升本考情分析-计算机基础.pdf.pdf','2026真题分析，模块比例与官方基本一致']
]; analysis.getRange('A4:H6').format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},verticalAlignment:'center',wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
for(const [c,w] of Object.entries({A:12,B:30,C:42,D:34,E:34,F:38,G:34,H:28})) analysis.getRange(`${c}:${c}`).format.columnWidth=w;
const out1=await SpreadsheetFile.exportXlsx(plan); await out1.save(planPath);

const scopePath=`${dir}/四川专升本_三科范围与资料清单_官方要求版.xlsx`;
const swb=await SpreadsheetFile.importXlsx(await FileBlob.load(scopePath));
const scope=swb.worksheets.getItem('考试范围总览');
scope.getRange('A13:H16').values=[
 ['近年考情参考','高数2026：微分21%、多元15%、函数16%、线代18%；计算题有跨章融合','英语2026：词法语法20、阅读16、完形20、对话5、选词10、翻译5、写作1','计算机2026：单选20/多选10/判断15/填空10/简答3/设计2','用途：调整复习和训练形式','来源：三份2026考情分析PDF','性质：趋势参考，不替代官方大纲','2027报考前核对最新真题与通知'],
 ['高数训练调整','重点：导数与应用、二重积分、级数和函数、矩阵综合','难点：极限、导数定义、积分、二重积分、线代','安排：章节题+跨章小题+限时套题','高数约80%、线代约20%','资料：26四川专升本考情分析-高等数学.pdf.pdf','',''],
 ['英语训练调整','重点：复合从句、非谓语、阅读主旨/推理、完形语境','难点：词汇搭配、长难句、词形转换、应用文格式','安排：每日词汇；每周阅读3篇、翻译1次、写作1次','客观题约70%、主观题约30%','资料：26四川专升本-考情分析-大学英语.pdf.pdf','',''],
 ['计算机训练调整','重点：办公自动化35%，软硬件20%，基础15%','难点：Office综合操作、网络安全、流程图、SQL','安排：先Office实操，再算法/网络/数据库，最后综合应用','主观题情境化趋势需重视','资料：26四川专升本考情分析-计算机基础.pdf.pdf','','']
];
scope.getRange('A13:H16').format={fill:'#F3F7FB',font:{color:'#1F2937',size:10},verticalAlignment:'center',wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
for(const [c,w] of Object.entries({A:16,B:38,C:38,D:38,E:32,F:40,G:30,H:28})) scope.getRange(`${c}:${c}`).format.columnWidth=w;
const reg=swb.worksheets.getItem('资料清单'); reg.getRange('A13:G15').values=[
 ['高数','2026考情分析PDF','识别高频与跨章节题型；不替代官方考纲','12月起','每周1套限时+跨章错题','进行中','重点关注微分、多元、级数、矩阵综合'],
 ['英语','2026考情分析PDF','按题型训练词法、阅读、完形、翻译、写作','9/1起','每周阅读3篇+翻译/写作各1次','进行中','题型可能年度调整'],
 ['计算机','2026考情分析PDF','按模块比例安排Office和综合应用训练','9/1起','每周1次Office实操','进行中','办公自动化35%优先']
];
const out2=await SpreadsheetFile.exportXlsx(swb); await out2.save(scopePath);
console.log('updated in place');
