$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root "tools\katago\opencl\katago.exe"
$model = Join-Path $root "models\katago\kata1-b18c384nbt-s9372115968-d4150170048.bin.gz"
$config = Join-Path $root "config\katago-gtp.cfg"

if (!(Test-Path $exe)) {
  throw "KataGo executable not found: $exe"
}
if (!(Test-Path $model)) {
  throw "KataGo model not found: $model"
}
if (!(Test-Path $config)) {
  throw "KataGo config not found: $config"
}

& $exe gtp -model $model -config $config
