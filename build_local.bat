@echo off
set VERSION=%1
if "%VERSION%"=="" set VERSION=0.0.18
python build.py --version %VERSION%
