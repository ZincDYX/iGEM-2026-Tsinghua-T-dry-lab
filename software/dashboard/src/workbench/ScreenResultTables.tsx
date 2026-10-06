import {show} from "../contracts/resultAdapters";

export function M1Matrix({records}:{records:Record<string,unknown>[]}) {
  return <div className="table-scroll"><table><thead><tr><th>候选 / 构建</th><th>linker / IDR（不同类别）</th><th>原规则判定 / 准入</th><th>原风险 / 缺预测证据</th><th>后端工程优先分</th></tr></thead>
    <tbody>{records.map((row,index)=><tr key={index}><td>{show(row.candidate_id)} / {show(row.construct_id)}</td><td>{show(row.linker_id)} / {show(row.idr_id)}</td><td>{show(row.sequence_screen_verdict)} / {show(row.eligibility)}</td><td>{show(row.screen_flags)} / {show(row.missing_predictor_evidence)}</td><td>{show(row.engineering_priority_score)}</td></tr>)}</tbody></table>
    <p>保留后端原顺序，不在前端另算排名；当前页的候选，不是完整候选库。</p>
  </div>;
}

export function M2Metrics({record}:{record:Record<string,unknown>}) {
  const fields=[
    ["core_ca_rmsd_angstrom","核心 Cα RMSD (Å)"],["pocket_rmsd_angstrom","口袋 RMSD (Å)"],
    ["pocket_sasa_retention","口袋 SASA 保留比"],["tail_pocket_min_distance_angstrom","尾部–口袋最短距离 (Å)"],
    ["clash_count","clash 数量"],["clash_cutoff_angstrom","原 clash 截断 (Å)"],
    ["s_sh3","SH3 位点计数"],["s_pdz","PDZ 位点计数"],["site_count_basis","位点计量基准"],
    ["eta_acc_sh3","SH3 可达系数"],["eta_acc_pdz","PDZ 可达系数"],
    ["v_scaffold_nm3","支架体积 (nm³)"],["v_enzyme_nm3","酶体积 (nm³)"],
  ];
  return <><p>参考身份：{show(record.reference_structure_id)} · 原文件 SHA-256 {show(record.reference_artifact_sha256)}</p>
    <p>结构来源 {show(record.structure_source_tool)} / {show(record.structure_source_tool_version)} · 负筛 {show(record.screen_verdict)} · 置信门控 {show(record.confidence_gate)}</p>
    <table><thead><tr><th>原定义 / 单位</th><th>后端原值</th></tr></thead><tbody>{fields.map(([key,label])=><tr key={key}><td>{label}</td><td>{show(record[key])}</td></tr>)}</tbody></table>
    <p>缺失指标：{show(record.missing_metrics)} · 体积方法：{show(record.volume_method)}</p>
  </>;
}
