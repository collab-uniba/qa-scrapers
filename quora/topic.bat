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
ECHO third:'URL' url of Organize-Topic to obtain the list of topics (Example:https://www.quora.com/topic/Computer-Programming/organize)
ECHO.
GOTO begin

:Param
SET /P EMAIL=Enter EMAIL:
SET /P PASSW=Enter PASSWORD:
SET /P URL=Enter URL-ORGANIZE_TOPIC (Example:https://www.quora.com/topic/Computer-Programming/organize):

cd Project_Quora
cd Project_Quora
cd spiders
cd topic
python topic.py %EMAIL% %PASSW% %URL%
pause