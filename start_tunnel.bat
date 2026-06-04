@echo off
set FLASK_APP=run.py
set FLASK_ENV=development
set FLASK_DEBUG=1

echo [TicketFlow] Nettoyage des anciennes instances...
taskkill /f /im python.exe > nul 2>&1

echo [TicketFlow] 1. Demarrage du serveur Flask en arriere-plan...
start /b "Flask Server" .\src\venv\Scripts\python.exe -m flask run

echo [TicketFlow] Attente de 3 secondes pour laisser le serveur demarrer...
timeout /t 3 /nobreak > nul

echo [TicketFlow] 2. Ouverture du tunnel completement prive avec Serveo...
echo [TicketFlow] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo [TicketFlow] Lisez bien la console ci-dessous.
echo [TicketFlow] Serveo va generer une ligne verte ressemblant a :
echo [TicketFlow] "Forwarding HTTP traffic from https://[UN_NOM].serveo.net"
echo [TicketFlow] C'est ce lien exact qu'il faut donner.
echo [TicketFlow] Votre IP restera 100%% anonyme.
echo [TicketFlow] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo.

ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:5000 serveo.net

echo.
echo [TicketFlow] Tunnel ferme.
echo [TicketFlow] Fermeture du serveur local...
taskkill /f /im python.exe > nul 2>&1
pause