@ECHO OFF
CLS

IF "%~1"=="-h" GOTO Help

:begin
ECHO 1.Help
ECHO 2.Insert Parameters
ECHO.

CHOICE /C 12 /M "Enter your choice:"

:: Note - list ERRORLEVELS in decreasing order
IF ERRORLEVEL 2 GOTO Param
IF ERRORLEVEL 1 GOTO Help

:Help
ECHO List of Parameters:
ECHO first:'EMAIL' related to Quora account
ECHO second:'PASSWORD' related to Quora account
ECHO third:'DB' choose a name for your database of items
ECHO.
GOTO begin

:Param
SET /P EMAIL=Enter EMAIL:
SET /P PASSW=Enter PASSWORD:
SET /P DB=Enter database:


cd Project_Quora
cd Project_Quora
cd spiders
scrapy crawl quora -a database=%DB% -a email=%EMAIL% -a password=%PASSW%
pause

