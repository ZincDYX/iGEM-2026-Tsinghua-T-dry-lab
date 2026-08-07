param(
  [string]$Python = 'python',
  [string]$Root = '.',
  [int]$Lpp = 50,
  [int]$Front = 30,
  [int]$Back = 30,
  [string]$OutDir = 'docs/softcopy'
)
& $Python tools/export_softcopy.py --root $Root --lpp $Lpp --front $Front --back $Back --outdir $OutDir
