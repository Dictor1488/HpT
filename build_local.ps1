param(
  [string]$Version = "0.0.52",
  [string]$Python27 = ""
)

$ErrorActionPreference = "Stop"
if ($Python27 -ne "") {
  python .\build.py --version $Version --python $Python27
} else {
  python .\build.py --version $Version
}
