@echo off
ECHO Activating virtual environment and starting the XML Search App...

REM Check if venv exists
IF NOT EXIST .\venv\Scripts\activate.bat (
    ECHO ERROR: Virtual environment (venv) not found in the current directory.
    ECHO Please run the setup instructions in README.md first.
    PAUSE
    EXIT /B 1
)

REM Activate virtual environment
CALL .\venv\Scripts\activate.bat

REM Check if src directory and gui.py exist
IF NOT EXIST .\src\gui.py (
    ECHO ERROR: src\gui.py not found.
    ECHO Ensure the project structure is correct.
    PAUSE
    EXIT /B 1
)

REM Navigate to src directory and run the Python GUI script
ECHO Starting GUI...
CD .\src
python gui.py
CD ..

REM Deactivate (optional, usually happens when cmd window closes)
REM CALL .\venv\Scripts\deactivate.bat

ECHO Application closed.
REM PAUSE
