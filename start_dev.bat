@echo off
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1
echo [TicketFlow] Demarrage du serveur de developpement avec rechargement automatique...
.\src\venv\Scripts\python.exe -m flask run
pause