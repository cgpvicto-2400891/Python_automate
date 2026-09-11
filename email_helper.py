"""
Envoi du résumé par courriel.
================================
Utilise smtplib (inclus dans Python, pas besoin de librairie externe).
Fonctionne avec Gmail via un "mot de passe d'application" :
https://support.google.com/accounts/answer/185833
(Nécessaire car Gmail bloque les connexions SMTP avec ton mot de passe normal.)
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")           # ton adresse courriel d'envoi
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")   # mot de passe d'application
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")  # adresse de M. Ali


def send_summary_email(summary: str):
    """Envoie le résumé de l'appel par courriel au propriétaire."""
    if not all([SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL]):
        print("[email_helper] Config SMTP incomplète — courriel non envoyé.")
        print("Résumé généré (non envoyé) :\n", summary)
        return

    msg = MIMEText(summary)
    msg["Subject"] = "CallAI — Résumé d'un appel reçu"
    msg["From"] = SMTP_USER
    msg["To"] = RECIPIENT_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print("[email_helper] Résumé envoyé avec succès.")
    except Exception as e:
        print(f"[email_helper] Échec de l'envoi du courriel : {e}")