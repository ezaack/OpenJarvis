@echo off
setlocal
set "SRC=%~dp0..\src"
uv run --project "%SRC%" jarvis %*
