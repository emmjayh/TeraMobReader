@echo off
ECHO Activating virtual environment and starting the XML Search App...

REM Check if venv exists
IF NOT EXIST .\venv\Scripts\activate.bat GOTO VenvError
GOTO VenvOk
:VenvError
ECHO.
ECHO ERROR: Virtual environment (venv) not found in the current directory (expected .\venv\).
ECHO Please run the setup instructions in README.md to create the venv first.
PAUSE
EXIT /B 1
:VenvOk

REM Check if src directory and gui.py exist
IF NOT EXIST .\src\gui.py GOTO GuiError
GOTO GuiOk
:GuiError
ECHO.
ECHO ERROR: Main script (src\gui.py) not found.
ECHO Ensure the project structure is correct and you are in the project root.
PAUSE
EXIT /B 1
:GuiOk

ECHO Activating virtual environment...
CALL .\venv\Scripts\activate.bat

ECHO Starting GUI from src directory...
CD .\src
python gui.py
CD ..

REM Optional: Deactivate, though closing the window typically handles this.
REM IF EXIST .\venv\Scripts\deactivate.bat CALL .\venv\Scripts\deactivate.bat

ECHO Application closed.
REM Adding a PAUSE here so if python script exits immediately with an error, window stays open.
PAUSE
