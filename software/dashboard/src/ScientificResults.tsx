import type { Run } from "./types";

export function ScientificResults({ run }: { run: Run }) {
  const assemblies = run.nodes.filter(
    (node) => node.parent_id === "assemblies" && node.status === "succeeded",
  );
  const pathway = run.nodes.find(
    (node) => node.id === "pathway" && node.status === "succeeded",
  )?.output;
  return (
    <>
      {assemblies.length > 0 && (
        <section className="card">
          <h2>自组装组成核验</h2>
          <table>
            <thead>
              <tr>
                <th>方案</th>
                <th>亚基组成</th>
                <th>总亚基数</th>
                <th>组装分子量 Da</th>
              </tr>
            </thead>
            <tbody>
              {assemblies.map((node) => (
                <tr key={node.id}>
                  <td>{String(node.output!.assembly_id)}</td>
                  <td>
                    {Object.entries(
                      node.output!.subunits as Record<string, number>,
                    )
                      .map(([id, count]) => `${id} × ${count}`)
                      .join(" + ")}
                  </td>
                  <td>{String(node.output!.total_subunits)}</td>
                  <td>{Number(node.output!.molecular_weight_da).toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">
            这是声明组成的核算，不是界面稳定性或自组装成功的预测。
          </p>
        </section>
      )}
      {pathway && (
        <section className="card">
          <h2>反应通路稳态</h2>
          <p>
            {pathway.status === "valid"
              ? "求解器收敛且所有稳态残差满足指定容差。"
              : "未获得符合容差的稳态：以下数值只能用于诊断，不能作为有效预测。"}
          </p>
          <p className="muted">{String(pathway.solver_message)}</p>
          <table>
            <thead>
              <tr>
                <th>物种</th>
                <th>平均浓度 μM</th>
                <th>浓相 μM</th>
                <th>稀相 μM</th>
                <th>外排 μM/h</th>
                <th>稳态残差 μM/h</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(
                pathway.concentrations_average_um as Record<string, number>,
              ).map(([species, average]) => (
                <tr key={species}>
                  <td>{species}</td>
                  <td>{average.toPrecision(5)}</td>
                  <td>
                    {(
                      pathway.concentrations_dense_um as Record<string, number>
                    )[species].toPrecision(5)}
                  </td>
                  <td>
                    {(
                      pathway.concentrations_dilute_um as Record<string, number>
                    )[species].toPrecision(5)}
                  </td>
                  <td>
                    {(
                      pathway.secretion_flux_um_per_h as Record<string, number>
                    )[species].toPrecision(5)}
                  </td>
                  <td>
                    {(pathway.residual_um_per_h as Record<string, number>)[
                      species
                    ].toExponential(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <h3>各反应总体通量</h3>
          <table>
            <thead>
              <tr>
                <th>反应</th>
                <th>通量 μM/h</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(
                pathway.reaction_flux_um_per_h as Record<string, number>,
              ).map(([reaction, flux]) => (
                <tr key={reaction}>
                  <td>{reaction}</td>
                  <td>{flux.toPrecision(5)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">
            使用上传的化学计量和两相竞争
            MM；参数来源及假设见复现信息。求解成功不等于模型已通过湿实验验证。
          </p>
        </section>
      )}
    </>
  );
}

export function ResultComparison({ runs }: { runs: Run[] }) {
  if (runs.length !== 2) return null;
  const metrics = runs.map(
    (run) =>
      new Map(
        run.nodes
          .filter(
            (node) =>
              node.parent_id === "sequences" && node.status === "succeeded",
          )
          .map((node) => [String(node.output!.id), node.output!]),
      ),
  );
  const shared = [...metrics[0].keys()].filter((id) => metrics[1].has(id));
  return (
    shared.length > 0 && (
      <>
        <h3>相同构建的结果对比</h3>
        <table>
          <thead>
            <tr>
              <th>构建</th>
              <th>前次分子量 Da</th>
              <th>后次分子量 Da</th>
              <th>前次 pI</th>
              <th>后次 pI</th>
            </tr>
          </thead>
          <tbody>
            {shared.map((id) => {
              const a = metrics[0].get(id)!.protparam as Record<string, number>;
              const b = metrics[1].get(id)!.protparam as Record<string, number>;
              return (
                <tr key={id}>
                  <td>{id}</td>
                  <td>{a.molecular_weight_da.toFixed(1)}</td>
                  <td>{b.molecular_weight_da.toFixed(1)}</td>
                  <td>{a.theoretical_pi.toFixed(2)}</td>
                  <td>{b.theoretical_pi.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </>
    )
  );
}
