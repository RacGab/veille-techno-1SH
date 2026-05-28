import json
import requests
import time
import os

API_URL = "http://127.0.0.1:5000/api/v1/triage"
TEST_FILE = os.path.join(os.path.dirname(__file__), 'data', 'billets_test.json')

def run_tests():
    print("Chargement des données de test...")
    try:
        with open(TEST_FILE, 'r', encoding='utf-8') as f:
            tickets = json.load(f)
    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier {TEST_FILE} est introuvable.")
        return

    total = len(tickets)
    reussites = 0

    print(f"\n=== Démarrage des tests sur {total} billets ===")
    print("Vérification que l'API est en ligne...")
    try:
        requests.get("http://127.0.0.1:5000/")
    except requests.exceptions.ConnectionError:
        print("❌ ERREUR: Impossible de se connecter à l'API.")
        print("💡 N'oubliez pas de lancer 'python app.py' dans un autre terminal d'abord !")
        return

    for i, ticket in enumerate(tickets):
        print(f"\n[{i+1}/{total}] Test du billet: {ticket['id']}")
        
        payload = {"description": ticket["description"]}
        
        try:
            # Envoi de la requête à notre API locale
            response = requests.post(API_URL, json=payload)
            
            if response.status_code == 201:
                result = response.json()
                cat_obtenue = result.get("categorie")
                prio_obtenue = result.get("priorite")
                justification = result.get("justification")
                
                cat_attendue = ticket["categorie_attendue"]
                prio_attendue = ticket["priorite_attendue"]
                
                # Vérification
                succes = (cat_obtenue == cat_attendue) and (prio_obtenue == prio_attendue)
                
                if succes:
                    reussites += 1
                    print("✅ SUCCÈS")
                else:
                    print("❌ ÉCHEC")
                
                print(f"   Attendu : {cat_attendue} | {prio_attendue}")
                print(f"   Obtenu  : {cat_obtenue} | {prio_obtenue}")
                print(f"   Raison  : {justification}")
                
            else:
                print(f"⚠️ Erreur de l'API ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            
        # Pause de 3 secondes entre chaque billet pour éviter l'erreur 429 (Quota API gratuit)
        time.sleep(3)

    # Bilan
    taux = (reussites / total) * 100
    print(f"\n=== Bilan Final ===")
    print(f"Réussites : {reussites}/{total} ({taux:.1f}%)")
    
    if taux >= 80:
        print("🏆 Objectif du MVP atteint (>= 80%) !")
    else:
        print("⚠️ Objectif non atteint.")

if __name__ == '__main__':
    run_tests()
