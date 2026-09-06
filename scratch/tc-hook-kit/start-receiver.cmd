@echo off
title tc-hook-kit receiver (127.0.0.1:8765)
echo ============================================
echo   tc-hook-kit receiver
echo   URL : http://127.0.0.1:8765
echo   Keep this window OPEN while running a task.
echo   Closing this window stops listening (events lost).
echo ============================================
python "D:\charles\program\ai\ai-eval-workspace\scratch\tc-hook-kit\server.py" --host 127.0.0.1 --port 8765
echo.
echo [receiver exited]
pause