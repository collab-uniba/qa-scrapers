@ECHO OFF
CLS

IF "%~1"=="-h" GOTO Help

:begin
ECHO.
ECHO.
ECHO ---- SCN Scraper ----
ECHO.
ECHO 1. NEW EXECUTION
ECHO 2. RESUME EXECUTION
ECHO 3. HELP
ECHO.
CHOICE /C 123 /M "Enter your choice: "

:: Note - list ERRORLEVELS in decreasing order
IF ERRORLEVEL 3 GOTO Help
IF ERRORLEVEL 2 GOTO Resume
IF ERRORLEVEL 1 GOTO New

:Help
ECHO.
ECHO -- HELP --
ECHO.
ECHO - If you would begin a new scraping process, press [1]
ECHO.
ECHO - If you want to delete the saved data of a previous execution beginning a new one, press [1]
ECHO.
ECHO - If you want to load a previous execution from the last page scraped, press [2].
ECHO.
pause
GOTO begin

:Resume
c:\python27\python.exe "%~dp0scnscraper\main.py" %*

:New
if exist "%~dp0scnscraper\abap.pydb" (
del "%~dp0scnscraper\abap.pydb"
del "%~dp0scnscraper\abap.json"
del "%~dp0scnscraper\index.txt" )
:: Edit index file with start URL PAGE
c:\python27\python.exe "%~dp0scnscraper\main.py" %*
PAUSE


