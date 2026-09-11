"""
Intégration avec le LLM (Anthropic Claude).
==============================================
Deux responsabilités :
1. Faire avancer la conversation : décider quelle question poser
   ensuite, ou confirmer que toutes les infos ont été recueillies.
2. Générer un résumé clair à la fin de l'appel.
"""

import os
import json
import anthropic
from dotenv import load_dotenv

from conversation import get_messages, mark_complete

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-5"  # ajuste selon le modèle disponible sur ton compte

OWNER_NAME = os.getenv("OWNER_NAME", "M. Ali")

SYSTEM_PROMPT = f"""Tu es l'assistant téléphonique de {OWNER_NAME}. Tu réponds aux
appels quand {OWNER_NAME} n'est pas disponible.

Ton objectif est de recueillir 3 informations auprès de l'appelant, dans un
français naturel et courtois, une question à la fois :
1. Le nom de l'appelant
2. Son numéro de téléphone (pour le rappeler)
3. La raison de son appel

Règles :
- Pose une seule question à la fois.
- Sois bref (1-2 phrases maximum), car tes réponses sont lues à voix haute.
- Dès que tu as les 3 informations, remercie poliment la personne et informe-la
  que {OWNER_NAME} la recontactera bientôt, puis termine la conversation.
- Ne pose jamais deux fois la même question si l'information est déjà connue.

Tu dois répondre UNIQUEMENT en JSON valide, sans aucun texte avant ou après,
au format exact suivant :
{{"reply": "ta phrase à dire à voix haute", "complete": true ou false}}

"complete" doit être true seulement quand tu viens de prononcer la phrase de
clôture (remerciement final), false sinon.
"""


def _build_conversation_text(call_sid: str) -> str:
    messages = get_messages(call_sid)
    lines = []
    for m in messages:
        speaker = "Appelant" if m["role"] == "caller" else "Assistant"
        lines.append(f"{speaker} : {m['text']}")
    return "\n".join(lines)


def get_next_question_or_confirmation(call_sid: str) -> str:
    """
    Envoie l'historique de la conversation au LLM et récupère
    la prochaine chose à dire à l'appelant.
    """
    conversation_text = _build_conversation_text(call_sid)

    user_prompt = f"""Voici la conversation jusqu'à maintenant :

{conversation_text}

Quelle est ta prochaine réponse ?"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text.strip()

    try:
        data = json.loads(raw_text)
        reply = data.get("reply", "Merci, pouvez-vous répéter?")
        complete = data.get("complete", False)
    except json.JSONDecodeError:
        # Filet de sécurité si le LLM ne respecte pas le format JSON
        reply = raw_text
        complete = False

    if complete:
        mark_complete(call_sid)

    return reply


SUMMARY_SYSTEM_PROMPT = f"""Tu rédiges un résumé clair et concis d'un appel
téléphonique reçu par l'assistant de {OWNER_NAME}. Le résumé sera envoyé par
courriel à {OWNER_NAME}.

Format attendu (texte simple, pas de JSON) :

Nom de l'appelant : ...
Numéro de téléphone : ...
Raison de l'appel : ...
Résumé : (2-3 phrases résumant la demande)
"""


def generate_summary(call_sid: str, caller_number: str) -> str:
    """
    Génère le résumé final de l'appel, à partir de l'historique complet
    de la conversation. Retourne None si la conversation était vide.
    """
    messages = get_messages(call_sid)
    if not messages:
        return None

    conversation_text = _build_conversation_text(call_sid)

    user_prompt = f"""Numéro de téléphone détecté par Twilio : {caller_number}

Transcription complète de l'appel :

{conversation_text}

Rédige le résumé selon le format demandé."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SUMMARY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text.strip()