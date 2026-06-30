# iGEM 2026 Tsinghua-T dry lab

面向“Corelets 相分离凝聚体 + SH3/PDZ 酶招募 + OptoQS”的可复现干实验起点。

当前仓库包含：

- 附件论文与开源代码的适用性审计；
- AF3/PDB 结果的口袋 RMSD、PAE、SASA 与距离指标框架；
- 具有质量守恒的 LLPS 两相 Michaelis-Menten 级联模型；
- 凝聚体体积分数和 OC:DMT 表达配比扫描；
- 固定上游提交的可靠第三方代码子模块。

## 先读结论

1. `DiffDock-PP` 是蛋白-蛋白刚性对接，不能替代酶-小分子对接；步骤 1.3 默认使用 AutoDock Vina。
2. 高跨域 PAE 只能说明相对构象不确定，不能单独证明 linker “工作良好”。应与 pocket RMSD、SASA、碰撞率及 MD 联合判断。
3. 酵母没有细菌式 RBS。表达比例应通过启动子、5'UTR、拷贝数、降解标签或基因组位点调节。
4. “150 倍富集”不能直接无条件乘到 `Vmax` 上；必须同时满足酶总量守恒、相体积分数和底物分配。本仓库的模型已按两相质量守恒处理。
5. 目前缺少 OC/DMT 序列、活性位点残基、底物结构和动力学参数，所以仓库只能提供可运行框架，不能诚实地给出“3:1”这一项目特异结论。
6. OptoQS 的持续转录不会自动维持 iLID-SspB 结合；原始 Corelets 关光后解聚，需要周期照明或改成不依赖持续光的装配模块。

详细审计见 [docs/literature_code_audit.md](docs/literature_code_audit.md)，模型假设见 [docs/modeling_notes.md](docs/modeling_notes.md)。

## 安装与测试

```bash
python -m venv .venv
python -m pip install -e ".[test,plot,sasa]"
pytest
```

## 运行示例

```bash
python scripts/sweep_kinetics.py --output results/example_sweep
```

输出包括配比扫描 CSV、体积分数扫描 CSV 和曲面图。示例参数仅用于验证代码，不代表光甘草定通路的真实参数。

## 推荐的实际建模对象

不要把所有部件误合并成单条 `enzyme-linker-SH3/PDZ-FTH1`：更符合 Corelets 架构的拆分是：

- Core：`FTH1-iLID` 24 聚体；
- Condensate module：`SspB-IDR-(SH3/PDZ)n`；
- Enzyme clients：`OC-linker-ligand` 与 `DMT-linker-ligand`。

因此结构筛查至少要分别评估酶-配体标签融合、IDR-招募域融合，以及放入 24 聚体后的空间碰撞。
