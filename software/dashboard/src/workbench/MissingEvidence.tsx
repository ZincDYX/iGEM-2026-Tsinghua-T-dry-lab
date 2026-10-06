import {show} from "../contracts/resultAdapters";

const stageGuidance:Record<string,{source:string;condition:string;next:string}>={
  M1:{source:"实际构建序列 / 测序 DNA、基因型、定位说明及相应预测器原输出",condition:"片段与完整融合体身份、定位语境、禁用限制位点",next:"补齐同一构建的原文件与工具证据；保留未确认构建标记。"},
  M2:{source:"结构与参考文件、残基映射、SASA / 几何输入和工具版本",condition:"与 M1 构建和序列 hash 对应；Q1–Q4 置信与否决门控保持",next:"先处理上游构建缺项，再上传同身份结构证据。"},
  M3:{source:"表达量 / 体积、招募位点、Kd、酶分配、相体积与密度来源",condition:"浓度单位、位点计量基准、温度 / pH / 条件相容",next:"补充带来源和条件的参数记录；不以默认浓度或 K=1 代替。"},
  M4:{source:"相容反应动力学、可用酶 / 相活性、Kp、运输及边界证据",condition:"宿主、assay、pH、温度、condition ID、检测 / 表达模式、进料及稳态适用范围",next:"逐反应补齐相容记录并重审；缺参数不借用其他反应值。"},
  M5:{source:"WetLabResult 原测量、身份、单位、时间、重复与 QC",condition:"构建与实验条件匹配；拟合候选和已批准参数分开",next:"导入真实测量并检查 QC；批准参数后创建迭代、重新审阅。"},
};
export function MissingEvidence({module,missing,status}:{module:string;missing:unknown;status:unknown}){
  const items=Array.isArray(missing)?missing.filter((item):item is string=>typeof item==="string"):[];
  if(!items.length&&status!=="insufficient_data")return null;
  const guidance=stageGuidance[module];
  return <section className="missing-evidence" aria-label={`${module} 缺项与下一步`}><h3>{module} · 科学数据不足</h3>
    <p>以下代码来自后端门控，不因作业完成而消失；空列表也不代表证据已批准。</p>
    {items.length?<ul>{items.map((item,index)=><li key={index}><code>{item}</code></li>)}</ul>:<p>当前候选没有提供逐项列表；请查看原 warning / 上游诊断。</p>}
    <dl><dt>所需来源类型</dt><dd>{guidance?.source??"该阶段原始证据"}</dd><dt>需要核对的条件</dt><dd>{guidance?.condition??"原结果声明范围"}</dd><dt>下一步</dt><dd>{guidance?.next??"补齐后重新审阅；不自动填值。"}</dd></dl><p>原状态：{show(status)}</p>
  </section>;
}
