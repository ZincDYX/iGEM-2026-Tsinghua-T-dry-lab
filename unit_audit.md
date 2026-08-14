# Galatea M3/M4 unit audit

| Parameter family | Status | Evidence / handling |
|---|---|---|
| Author total time | verified | `simulation-data.txt` labels `total_time = 5 | day`. The reference adapter retains this author time axis. |
| Author initial compound 8 | author_native_only | Value `7.4e-5` is used unchanged in the reference adapter; a physical concentration unit is not verified. |
| Author Km values | author_native_only | Numeric values are supplied in `simulation-data.txt`; their mapping to uM/mM is unresolved. |
| Author kcat/Km and derived kcat | author_native_only | The reference code computes `kcat = (kcat/Km) * Km`; physical time and concentration dimensions are not verified. |
| Author enzyme scale E | author_native_only | `E = 0.01` is an author-model scale and is not a measured Galatea abundance. |
| Author transport rate | unresolved | `rate = 2` is used only in author-native reference reproduction. Physical transport units are not established. |
| `Source Data_V2.xlsx` | unresolved for model units | The workbook was inspected as supporting source data (48 figure sheets); it does not by itself establish the author model's concentration, enzyme-scale, or transport unit mapping. |
| Physical Galatea enzyme abundance | reviewed physical input required | Physical production mode accepts only reviewed `uM` abundance records. |
| Author-native enzyme scales | author_native_only | `ptr_scale`/`pt_scale`/`oc_scale`/`dmt_scale` are explicit relative scales, never measured `uM` abundance. |
| Galatea phi and metabolite Kp | dimensionless sensitivity input | Both modes require provenance-bearing dimensionless records; their source may be reviewed evidence or explicitly allowed sensitivity assumptions. |
| Recruitment ratio/fraction/bias | dimensionless sensitivity input | Engineering design/sensitivity inputs, not measured binding thermodynamics unless separately evidenced. |

Consequently, author-native Galatea runs support normalized/relative sensitivity only and must block absolute uM/h, mM, physical-rate, productivity, or titer claims until an explicit unit mapping is sourced and reviewed. Physical mode remains a separate reviewed-parameter path.
