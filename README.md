# CallAI — Guide de démarrage

Assistant téléphonique intelligent en Python (Flask + Twilio + Claude).

## Structure du projet

```
app.py             Serveur Flask, routes webhook Twilio
conversation.py     Mémoire des conversations en cours (par CallSid)
llm_helper.py       Appels au LLM (Claude) : questions + résumé
email_helper.py     Envoi du résumé par courriel
requirements.txt    Dépendances Python
.env.example         Modèle des variables d'environnement
```

## 1. Installation

```bash
python -m venv venv
source venv/bin/activate      # sur Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Remplis ensuite le fichier `.env` avec :
- Ta clé API Anthropic (console.anthropic.com)
- Un mot de passe d'application Gmail (voir lien dans `email_helper.py`)
- Le courriel du destinataire du résumé

## 2. Lancer le serveur localement

```bash
python app.py
```

Le serveur tourne sur `http://localhost:5000`.

## 3. Exposer ton serveur local à Internet avec ngrok

Twilio a besoin d'une URL publique pour t'envoyer les webhooks. En développement,
on utilise **ngrok** pour exposer ton `localhost` temporairement.

```bash
# installation (une fois)
# macOS : brew install ngrok
# sinon : https://ngrok.com/download

ngrok http 5000
```

ngrok t'affiche une URL du type `https://abcd1234.ngrok-free.app` — garde-la, tu
en as besoin à l'étape suivante. **Elle change à chaque redémarrage de ngrok**
(sauf compte payant), donc il faudra remettre à jour la config Twilio si tu
relances ngrok.

## 4. Configurer ton numéro Twilio

1. Va sur [console.twilio.com](https://console.twilio.com) → Phone Numbers → ton numéro
2. Dans la section **Voice Configuration** :
   - "A call comes in" → Webhook → `https://TON-URL-NGROK.ngrok-free.app/voice` → HTTP POST
   - "Call status changes" (statusCallback) → `https://TON-URL-NGROK.ngrok-free.app/call-status` → HTTP POST
3. Sauvegarde

## 5. Tester avec ton numéro personnel (renvoi d'appel)

Pour tester avec ton vrai numéro plutôt que le numéro Twilio directement :

- Configure un **renvoi d'appel conditionnel** depuis ton téléphone vers le
  numéro Twilio (ex: renvoi si non-réponse). La procédure exacte dépend de ton
  opérateur (Bell, Rogers, Vidéotron, etc.) — demande-moi si tu veux la
  marche à suivre précise pour le tien.

Ou plus simple pour commencer : **appelle directement le numéro Twilio** pour
valider que tout fonctionne, avant de te soucier du renvoi depuis ton numéro
personnel.

## 6. Déroulement d'un appel de test

1. Appelle le numéro Twilio
2. L'assistant se présente et demande comment il peut t'aider
3. Réponds à voix haute (nom, numéro, raison de l'appel)
4. Une fois les 3 informations recueillies, l'assistant remercie et raccroche
5. Un résumé est envoyé par courriel au destinataire configuré

## Dépannage courant

- **Rien ne se passe à l'appel** → vérifie que ngrok tourne et que l'URL dans
  Twilio correspond exactement à celle affichée par ngrok (elle change à
  chaque redémarrage de ngrok).
- **Erreur 500 dans les logs Flask** → regarde le terminal où `python app.py`
  tourne, l'erreur Python complète s'y affiche.
- **Le courriel n'arrive pas** → vérifie le mot de passe d'application Gmail
  (pas ton mot de passe normal), et regarde les logs Flask pour l'erreur SMTP.
- **La reconnaissance vocale comprend mal** → `language="fr-CA"` est déjà
  configuré dans le code ; parle clairement et évite les environnements bruyants
  pour tes tests.

## Prochaines améliorations possibles (hors scope du prototype de base)

- Remplacer le dictionnaire en mémoire par Redis (survit aux redémarrages)
- Ajouter une gestion des cas d'erreur (appelant raccroche en plein milieu)
- Déployer sur un serveur (Render, Railway, Fly.io) pour avoir une URL fixe
  au lieu de ngrok