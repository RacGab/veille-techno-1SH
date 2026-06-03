@echo off
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1
echo [TicketFlow] Demarrage du serveur en mode RESEAU LOCAL...
echo [TicketFlow] Vous etes prets pour la demonstration !
echo [TicketFlow] Votre professeur peut y acceder depuis son ordinateur (si connecte au meme reseau) avec l'une de ces adresses :
echo.
echo    1. http://%COMPUTERNAME%:5000
echo    2. http://192.168.2.14:5000
echo.
.\src\venv\Scripts\python.exe -m flask run --host=0.0.0.0
pause