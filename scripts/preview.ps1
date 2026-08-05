param(
    [int]$Port = 8080,
    [switch]$NoOpen
)

$docsPath = Resolve-Path (Join-Path $PSScriptRoot "..\\docs")
$url = "http://localhost:$Port/"

if (-not $docsPath) {
    Write-Error "Could not find docs folder."
    exit 1
}

Push-Location $docsPath
try {
    if (-not $NoOpen) {
        Start-Process $url
    }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -m http.server $Port
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        python -m http.server $Port
    }
    else {
        Write-Error "Python is required for local preview. Install Python 3 and rerun this script."
        exit 1
    }
}
finally {
    Pop-Location
}