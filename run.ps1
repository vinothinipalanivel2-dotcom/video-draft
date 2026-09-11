<#
.SYNOPSIS
    Developer helper script for video-draft pipeline.
.DESCRIPTION
    Provides clean reproduction shortcuts for Windows environments.
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("install", "test", "run", "benchmark", "validate", "clean", "help")]
    [string]$Command = "help"
)

switch ($Command) {
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Cyan
        python -m pip install -r requirements-dev.txt
        python -m pip install -e .
    }
    "test" {
        Write-Host "Running test suite..." -ForegroundColor Cyan
        python -m pytest tests/ -v
    }
    "run" {
        Write-Host "Running baseline pipeline..." -ForegroundColor Cyan
        python -m video_draft.cli run --brief configs/briefs/baseline_16x9.json
    }
    "benchmark" {
        Write-Host "Running benchmark..." -ForegroundColor Cyan
        python -m video_draft.cli benchmark --brief configs/briefs/baseline_16x9.json
    }
    "validate" {
        Write-Host "Validating baseline brief..." -ForegroundColor Cyan
        python -m video_draft.cli validate --brief configs/briefs/baseline_16x9.json
    }
    "clean" {
        Write-Host "Cleaning cache..." -ForegroundColor Cyan
        Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force
        Get-ChildItem -Path . -Filter "*.egg-info" -Recurse -Force | Remove-Item -Recurse -Force
    }
    Default {
        Write-Host "Usage: .\run.ps1 [install | test | run | benchmark | validate | clean]" -ForegroundColor Yellow
    }
}
