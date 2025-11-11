@echo off
REM Activate virtual environment and run hybrid_chunking.py

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Running hybrid_chunking.py...
python hybrid_chunking.py

echo.
echo Done! Check the outputs folder for results.
pause
