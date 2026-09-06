import { FileBlob, SpreadsheetFile } from '@oai/artifact-tool';
const dir='D:/专升本学习/outputs';
const planPath=`${dir}/四川专升本_9-10月可编辑计划_修正版_v2.xlsx`;
const plan=await SpreadsheetFile.importXlsx(await FileBlob.load(planPath));
const intro=plan.worksheets.getItem('使用说明');
intro.getRange('A13:B17').values=[
 ['官方考试依据','四川省教育厅《关于印发四川省2024年普通高校专升本考试要求的通知》（2021-08-05）'],
 ['高数考试','闭卷笔试，150分/120分钟；高数约80%，线性代数约20%'],
 ['英语考试','闭卷笔试，150分/120分钟；约3500常用词；客观题约70%、主观题约30%'],
 ['计算机考试','闭卷笔试，150分/120分钟；办公自动化约35%，软硬件约20%，基础知识约15%'],
 ['计划原则','9-10月先按官方模块建立基础；报考专业和2027最新通知发布后，再核对是否有调整']
];
intro.getRange('A13:A17').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
intro.getRange('B13:B17').format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
intro.getRange('A13:B17').format.rowHeight=34;
const stage=plan.worksheets.getItem('阶段与周计划');
stage.getRange('C4:E7').values=[
 ['函数、极限、连续、导数基础；同步线代行列式/矩阵入门','3500词分批启动；阅读主旨与细节；翻译/写作基础','计算机基础15%：概述、数制、软硬件；办公自动化35%入门'],
 ['一元函数微分与积分；线代矩阵、方程组；每周小测','词汇+阅读；每周1次英译汉/汉译英或100词写作','Windows与Office重点操作；每周完成1次表格/文档练习'],
 ['积分、向量空间解析几何；线代向量与方程组','长难句、阅读推断；听力跟读；翻译写作轮换','网络与信息安全10%；算法与程序设计10%入门'],
 ['综合题与章节串联；保留线代20%权重训练','按题型轮换训练；作文不少于100词；计时阅读','数据库5%、新技术5%；综合应用题与错题回炉']
];
const scopePath=`${dir}/四川专升本_三科范围与资料清单.xlsx`;
const swb=await SpreadsheetFile.importXlsx(await FileBlob.load(scopePath));
const s=swb.worksheets.getItem('考试范围总览');
s.getRange('A4:H6').values=[
 ['高数','有基础但久未接触','函数/极限/连续、微分、积分；线代行列式/矩阵入门','向量与空间解析几何、多元函数、二重积分、级数、微分方程；线代向量/方程组','综合题、真题、限时训练；线代约20%固定保留','宋浩四川专升本指导丛书、上一届资料','150分/120分钟；高数约80%，线代约20%；闭卷笔试','官方高数PDF：edu.sc.gov.cn/.../2.四川省普通高校专升本《高等数学》考试要求.pdf'],
 ['英语','四级380；阅读尚可，词汇/听力/作文翻译弱','约3500词；语法22项；阅读主旨/细节；英汉互译；100词写作','题型轮换：补全对话、词汇语法、阅读、选词/选句、完形、改错、翻译、写作','真题计时；客观题约70%，主观题约30%；写作不少于100词','上一届资料；自建词汇表','150分/120分钟；闭卷笔试；以官方题型抽取组卷','官方英语PDF：edu.sc.gov.cn/.../3.四川省普通高校专升本《大学英语》考试要求.pdf'],
 ['计算机','零基础但预计提分快','基础知识15%；软硬件基础20%；办公自动化35%','网络安全10%；算法程序10%；数据库5%；云/大数据/物联网/AI共5%','按模块刷题；Office综合操作；闭卷综合题','网课资源、上一届资料','150分/120分钟；题型可含选择、多选、判断、填空、简答、设计、综合应用','官方计算机PDF：edu.sc.gov.cn/.../4.四川省普通高校专升本《计算机基础》考试要求.pdf']
];
const exam=swb.worksheets.getItem('考试范围总览');
exam.getRange('A8:H8').values=[['统一考试信息','高数','英语','计算机','形式','分值','时间','备注']];
exam.getRange('A9:H9').values=[['2024官方要求','闭卷笔试','闭卷笔试','闭卷笔试','三科均为笔试','各150分','各120分钟','2027年报考前需再次核对最新通知']];
exam.getRange('A11:H11').values=[['计算机模块比例','基础知识15%','软硬件20%','办公自动化35%','网络安全10%','算法10%','数据库5%','新技术5%']];
exam.getRange('A8:H8').format={fill:'#D9EAF7',font:{bold:true,color:'#17365D'},horizontalAlignment:'center',wrapText:true,borders:{preset:'all',style:'thin',color:'#B7C9D6'}};
exam.getRange('A9:H9').format={fill:'#FFFFFF',font:{color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
exam.getRange('A11:H11').format={fill:'#E2F0D9',font:{bold:true,color:'#1F2937',size:10},wrapText:true,borders:{preset:'inside',style:'thin',color:'#D9E2F3'}};
const reg=swb.worksheets.getItem('核对记录');
reg.getRange('A4:E6').values=[
 ['高数','四川省普通高校专升本《高等数学》考试要求','2021-08-05','高数+线性代数；150分/120分钟；线代约20%','https://edu.sc.gov.cn/scedu/c100495/2021/8/5/0fb9140b78414a36899ae0faf30c30de.shtml'],
 ['英语','四川省普通高校专升本《大学英语》考试要求','2021-08-05','约3500词；阅读/翻译/写作；150分/120分钟','https://edu.sc.gov.cn/scedu/c100495/2021/8/5/0fb9140b78414a36899ae0faf30c30de.shtml'],
 ['计算机','四川省普通高校专升本《计算机基础》考试要求','2021-08-05','七大模块比例；150分/120分钟；闭卷笔试','https://edu.sc.gov.cn/scedu/c100495/2021/8/5/0fb9140b78414a36899ae0faf30c30de.shtml']
];
const pOut=await SpreadsheetFile.exportXlsx(plan); await pOut.save(`${dir}/四川专升本_9-10月可编辑计划_官方要求版.xlsx`);
const sOut=await SpreadsheetFile.exportXlsx(swb); await sOut.save(`${dir}/四川专升本_三科范围与资料清单_官方要求版.xlsx`);
console.log('updated official versions');
