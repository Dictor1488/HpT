@echo off
set VERSION=%1
if "%VERSION%"=="" set VERSION=0.0.62
python build.py --version %VERSION%
