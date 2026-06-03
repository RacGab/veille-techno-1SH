@echo off
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo [TicketFlow] 1. Demarrage du serveur Flask en arriere-plan...
start /b "Flask Server" .\src\venv\Scripts\python.exe -m flask run

echo [TicketFlow] Attente de 3 secondes pour laisser le serveur demarrer...
timeout /t 3 /nobreak > nul

echo [TicketFlow] 2. Ouverture du tunnel securise avec localtunnel...
echo [TicketFlow] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo [TicketFlow] ATTENTION : La premiere fois, le site demandera un mot de passe.
echo [TicketFlow] Voici l'adresse IP (Endpoint IP) a entrer si demande :
curl -s https://loca.lt/mytunnelpassword
echo.
echo [TicketFlow] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo [TicketFlow] Votre site sera disponible a : https://ticketflow-demo.loca.lt
echo.
npx localtunnel --port 5000 --subdomain ticketflow-demo

echo [TicketFlow] Fermeture...
taskkill /f /im python.exe > nul 2>&1
pause