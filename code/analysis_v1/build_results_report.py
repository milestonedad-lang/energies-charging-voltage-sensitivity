from pathlib import Path
import json
import pandas as pd
P=Path(__file__).resolve().parents[1]
d=pd.read_csv(P/'results/all_scenarios.csv');m=d[d.setting=='main']
p=pd.read_csv(P/'results/paired_comparisons.csv');b=pd.read_csv(P/'results/no_EV_baselines.csv')
r=pd.read_csv(P/'results/conditional_temporal_resampling.csv');r=r[r.metric=='disagreement_rate']
g=json.loads((P/'evidence/validation_gate.json').read_text());ex=json.loads((P/'evidence/execution_summary.json').read_text())
def table(headers, rows):
 return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)
text='''# 交通—电力研究：潮流校验与正式结果报告 v1.0

本轮已按锁定方案完成数值校验、四组主对照、全部预定单因素敏感性分析，以及可选的配对时间分块重采样。结果支持继续开展论文写作，但贡献应限定为“开放充电电量表征对配电网电压约束判断的条件敏感性”。目前材料属于分析结果包，不是完整投稿稿件。

## 1. 数据、比较对象和固定设置

使用冻结的 UrbanEV 输入：2022-09-01至2023-02-28，181天、4344小时、275个区域。两份原始电量文件分别记作 A（volume.csv）和 B（volume-11kW.csv），均为估计电量表征，不作为计量真值。两者总电量比 A/B=2.422545；文件预处理差异尚未完全分离，因此不能把全部结果归因为某一11 kW假设。

B-G 为 B 乘以全局总电量比，使总电量与 A 相等；B-Z 为每一区域的 B 分别乘以该区域 A/B 总电量比，使每一区域全时段电量与 A 相等。这些是比较用控制输入，不是经验证的修正真值。

在33节点和69节点标准测试馈线上，采用平衡、径向、恒PQ稳态模型，源节点电压1 p.u.。主分析背景P/Q乘数β=0.5；EV功率因数1；电量按1小时换算功率，并以 A 聚合功率第99百分位 C=126.91314 MW 为共同锚点，缩放系数 c=0.25×馈线原始有功负荷/C。所有表征使用同一系数。区域按固定规则映射至非源节点，属于合成映射，不代表深圳实际配电接线。

小时“越限”定义为任一负荷节点电压低于0.95或高于1.05 p.u.；阈值由研究方案设定，不宣称对应当地强制标准。主要终点是同一小时两组输入的越限判断是否不同，而不是两个越限率简单相减。4344小时逐小时配对，全部保留。

## 2. 数值校验和无EV基线

前推回代法与独立实现的AC节点功率平衡非线性求解器交叉校验32个预先选定算例，全部通过。最大复数节点电压差为1.3540×10⁻¹² p.u.，低于预定1×10⁻⁷容差。两种方法共用同一网架数据和单位解析，因此这一结果说明数值实现一致，不能替代实测物理验证。

正式计算包含108个场景、469152个“场景—小时”，其中主对照34752个，未出现不收敛。正式计算最大节点功率残差4.6943×10⁻¹² p.u.；最大绝对有功平衡误差3.7333×10⁻⁹ kW。逐场景收敛记录、独立校验表与执行配置随包提供。

'''
text+=table(['馈线','背景乘数β','最低节点电压/p.u.','网损/kW','无EV是否低于0.95'],[[x.feeder,f'{x.beta:.1f}',f'{x.vmin_pu:.6f}',f'{x.loss_kW:.3f}','是' if x.violates_study_0p95 else '否'] for x in b.itertuples()])
text+='''
原始满背景负荷β=1时，两条馈线在没有EV的情况下已经低于0.95；不能将这种基线越限归因于充电。预先固定的主分析β=0.5时，两条馈线无EV基线均高于0.95。

## 3. 四组主对照

以下均为4344小时全记录的描述性结果。

'''
text+=table(['馈线','输入','越限小时数','越限小时比例','全记录最低电压/p.u.','平均最低电压/p.u.','平均网损/kW'],[[x.feeder,x.representation,x.voltage_violating_hours,f'{100*x.voltage_violating_hours/4344:.2f}%',f'{x.minimum_voltage_pu:.6f}',f'{x.mean_minimum_voltage_pu:.6f}',f'{x.mean_loss_kW:.3f}'] for x in m.itertuples()])
text+='''
## 4. 配对判断差异与等电量控制

配对不一致率=(仅A越限的小时数+仅另一输入越限的小时数)/4344。重采样范围使用2000次配对移动7天分块，固定种子20261106；整日保留所有区域及其配对输入，26块拼接后截取181天。范围为2.5%–97.5%分位数，仅描述现有记录及固定模型下的时间重采样变化，不是总体、全年或真实配电网的置信区间。

'''
rows=[]
for x in p[p.setting=='main'].itertuples():
 rr=r[(r.feeder==x.feeder)&(r.alternative==x.alternative)].iloc[0]
 rows.append([x.feeder,'A vs '+x.alternative,x.A_only_violating_hours,x.alternative_only_violating_hours,f'{x.disagreement_rate_lower*100:.2f}%',f'{rr.temporal_resampling_percentile_2p5*100:.2f}%–{rr.temporal_resampling_percentile_97p5*100:.2f}%'])
text+=table(['馈线','比较','仅A越限','仅另一输入越限','配对不一致率','条件时间重采样范围'],rows)
text+='''
原始A/B在33节点的83.68%不一致率远大于69节点的1.91%，不能泛化为所有电网的固定效应。全局等电量控制后，不一致率分别为12.62%和10.08%；此时B-G的越限小时反而多于A，提示简单的总电量缩放不能保留原来的时空负荷分配。

逐区域等电量控制后，不一致率仍为6.26%（272小时）和0.85%（37小时）。与此同时，B-Z相对A的平均最低电压差分别仅为+3.30×10⁻⁶和+1.01×10⁻⁷ p.u.。因此应突出“均值接近仍可能出现部分阈值判断变化”，不能表述为等电量之后仍有很大的平均电压效应。电压均值差和离散判断差异是不同终点。

## 5. 全部预定敏感性分析

以下单因素分析使用A/B；其他参数保持主分析设定。等电量输入B-G/B-Z在方案v1中未扩展到替代映射、负荷水平或功率因数，不能据本表宣称等电量结论具有这些稳健性。

'''
labels={'main':'主分析','alpha_010':'EV缩放α=0.10','alpha_050':'EV缩放α=0.50','beta_040':'背景β=0.40','beta_060':'背景β=0.60','pf_095':'EV滞后功率因数0.95'}
rows=[]
for s,l in labels.items():
 vals=[]
 for f in ['case33bw.m','case69.m']:
  v=p[(p.feeder==f)&(p.setting==s)&(p.alternative=='B')].iloc[0]
  vals.append(f'{100*v.disagreement_rate_lower:.2f}%')
 rows.append([l,*vals])
text+=table(['单因素设置','33节点A/B不一致率','69节点A/B不一致率'],rows)
text+='\n20次预设随机区域映射（映射种子20261105+映射编号）的结果：\n\n'
rows=[]
for f,q in p[p.setting.str.startswith('mapping')].groupby('feeder'):
 v=100*q.disagreement_rate_lower
 rows.append([f,f'{v.min():.2f}%–{v.max():.2f}%',f'{v.median():.2f}%'])
text+=table(['馈线','20映射A/B不一致率范围','中位数'],rows)
text+='''
映射变化可使69节点A/B不一致率达到22.95%，明显高于固定映射主分析的1.91%；说明网络和空间分配会改变结果。不能挑选某一映射作为普遍结论。

在主分析输出上，将下限改为0.90，两条馈线三种配对比较的不一致率全部为0；下限为0.94时，33节点A/B、A/B-G、A/B-Z分别为15.81%、12.98%、4.01%，69节点均为0。这说明“判断改变”与所选阈值及其附近的电压分布有关；0.90下不一致率为0不等于电压数值完全相同。

剔除两份电量文件零值状态不一致所涉及的31个完整小时后，剩余4313小时。33节点三种比较不一致率为83.96%、12.54%、6.24%；69节点为1.88%、10.09%、0.81%。这一排除规则不改变主分析的基本排序，但不能代表已处理所有潜在缺失或估计偏差。

## 6. 可支持的贡献及边界

本轮支持的贡献是：建立输入来源可追查、缩放和比较规则固定、逐小时配对的分析流程；以全局和区域总电量匹配控制检验“只看总电量是否足够”；通过测试馈线和预定敏感性展示电压阈值判断的条件依赖。

不支持的表述包括：某份文件是真实充电负荷、B比A更准确或更安全、发现了真实深圳配电网越限率、证明11 kW规则的因果影响，以及上述比例可以直接用于年度或其他城市的风险预测。

模型还未包含三相不平衡、调压器与控制策略、动态背景负荷、真实区域—馈线连接关系；算例RATE_A均为0，没有可用线路热容量上限，因此本研究不报告线路热越载风险。69节点结果属于标准测试网架重复分析，不属于跨城市实证验证。

## 7. 下一步

正式主分析已经完成。建议在现有结果基础上先做一项明确标记为方案v1.1的补充：把B-G/B-Z加入预定的20种替代映射，以检验论文核心的“等电量后仍有差异”是否依赖单一映射。该补充尚未执行，须与本轮预先固定结果分开记录；之后再完成Methods、Results及贡献与局限的初稿。论文的新颖性仍须对照已检索的文献逐条核查，不能以数值差异本身保证录用。

## 8. 文件与来源

本包包含所有108场景的逐小时NPZ结果、全场景CSV、主对照和配对差异表、数值门槛记录、运行版本、源代码、图1及其源数据、冻结方案和可复查输入原包。原始数据沿用原来源许可；无需提交账号或识别个人。

UrbanEV固定版本：44f2aa0c8d89f192bce00bafb0def74a21b39c68；网架来源MATPOWER固定版本：80b6e16f760f58721ad31221c7287c28259cd4ad。来源URL、单位检查及SHA256见方案原包和evidence。程序自行实现潮流，不需要MATLAB或MATPOWER运行环境。

分析方法参考：MATPOWER《Distribution Power Flow》https://matpower.app/manual/matpower/DistributionPowerFlow.html ；SciPy root官方说明 https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.root.html 。实际计算环境版本以evidence中的运行记录为准：Python3.12.14、NumPy2.3.5、pandas2.2.3、SciPy1.17.0。
'''
(P/'outputs/交通电力_潮流校验与正式结果_v1.md').write_text(text)
