# iGEM 2026 Tsinghua-T dry lab

面向“Corelets 相分离凝聚体 + SH3/PDZ 酶招募 + OptoQS”的可复现干实验起点。

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
