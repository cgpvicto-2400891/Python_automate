"""
CallAI - Serveur principal
===========================
Ce serveur reçoit les webhooks de Twilio quand un appel arrive,
gère la conversation avec l'appelant via le LLM, puis génère
et envoie un résumé par courriel une fois l'appel terminé.

Flux :
1. Twilio reçoit un appel -> POST /voice          (message d'accueil)
2. Twilio transcrit la voix -> POST /gather        (boucle de conversation)
3. Appel terminé -> POST /call-status              (résumé + courriel)
"""

import os
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

from conversation import (
    get_or_create_conversation,
    add_message,
    is_conversation_complete,
    end_conversation,
)
from llm_helper import get_next_question_or_confirmation, generate_summary
from email_helper import send_summary_email

load_dotenv()

app = Flask(__name__)

# Nom de la personne pour qui l'assistant répond (à personnaliser)
OWNER_NAME = os.getenv("OWNER_NAME", "M. Ali")


@app.route("/voice", methods=["POST"])
def voice():
    """
    Premier webhook appelé par Twilio dès que l'appel est décroché.
    On envoie le message d'accueil et on ouvre l'écoute avec <Gather>.
    """
    call_sid = request.form.get("CallSid")

    # On initialise une nouvelle conversation en mémoire pour cet appel
    get_or_create_conversation(call_sid)

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/gather",       # Twilio enverra la transcription ici
        method="POST",
        language="fr-CA",       # reconnaissance vocale en français québécois
        speech_timeout="auto",  # Twilio détecte automatiquement la fin de la phrase
    )
    gather.say(
        f"Bonjour, je suis l'assistant de {OWNER_NAME}. Comment puis-je vous aider aujourd'hui?",
        language="fr-CA",
        voice="Polly.Chantal",  # voix française naturelle (Amazon Polly via Twilio)
    )
    response.append(gather)

    # Si l'appelant ne dit rien du tout, on relance une fois
    response.redirect("/voice")

    return str(response)


@app.route("/gather", methods=["POST"])
def gather():
    """
    Appelé à chaque fois que Twilio a fini de transcrire une réponse
    de l'appelant. On fait avancer la conversation avec le LLM.
    """
    call_sid = request.form.get("CallSid")
    speech_result = request.form.get("SpeechResult", "")

    add_message(call_sid, role="caller", text=speech_result)

    # Le LLM décide : soit poser la prochaine question,
    # soit confirmer que toutes les infos ont été recueillies.
    assistant_reply = get_next_question_or_confirmation(call_sid)
    add_message(call_sid, role="assistant", text=assistant_reply)

    response = VoiceResponse()

    if is_conversation_complete(call_sid):
        # On remercie et on raccroche - le résumé sera généré
        # automatiquement au webhook /call-status quand Twilio
        # confirmera la fin de l'appel.
        response.say(assistant_reply, language="fr-CA", voice="Polly.Chantal")
        response.hangup()
    else:
        gather = Gather(
            input="speech",
            action="/gather",
            method="POST",
            language="fr-CA",
            speech_timeout="auto",
        )
        gather.say(assistant_reply, language="fr-CA", voice="Polly.Chantal")
        response.append(gather)
        response.redirect("/gather")  # si silence, on redemande

    return str(response)


@app.route("/call-status", methods=["POST"])
def call_status():
    """
    Webhook de statut d'appel configuré dans Twilio (statusCallback).
    Appelé quand l'appel se termine (completed, no-answer, busy, etc.).
    C'est ici qu'on génère le résumé final et qu'on l'envoie par courriel.
    """
    call_sid = request.form.get("CallSid")
    call_status_value = request.form.get("CallStatus")
    caller_number = request.form.get("From")

    if call_status_value == "completed":
        summary = generate_summary(call_sid, caller_number)
        if summary:
            send_summary_email(summary)

    # On libère la mémoire de conversation pour cet appel
    end_conversation(call_sid)

    return ("", 204)


@app.route("/", methods=["GET"])
def health_check():
    """Simple route pour vérifier que le serveur tourne."""
    return "CallAI est en ligne."


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)