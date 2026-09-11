"""
Gestion de l'état des conversations en cours.
===============================================
Chaque appel Twilio a un identifiant unique : le CallSid.
Comme chaque webhook Twilio est une requête HTTP indépendante,
on doit stocker l'historique de la conversation quelque part
entre chaque tour de parole. Pour un prototype, un simple
dictionnaire Python en mémoire suffit (pas besoin de base de données).

Limite à connaître : si le serveur redémarre, toutes les
conversations en cours sont perdues. Pour une vraie mise en
production, on remplacerait ceci par Redis ou une base de données.
"""

# Structure : { call_sid: { "messages": [...], "complete": False, "caller_number": "..." } }
_conversations = {}


def get_or_create_conversation(call_sid: str) -> dict:
    if call_sid not in _conversations:
        _conversations[call_sid] = {
            "messages": [],   # liste de {"role": "caller"/"assistant", "text": "..."}
            "complete": False,
        }
    return _conversations[call_sid]


def add_message(call_sid: str, role: str, text: str):
    conv = get_or_create_conversation(call_sid)
    conv["messages"].append({"role": role, "text": text})


def get_messages(call_sid: str) -> list:
    return get_or_create_conversation(call_sid)["messages"]


def mark_complete(call_sid: str):
    get_or_create_conversation(call_sid)["complete"] = True


def is_conversation_complete(call_sid: str) -> bool:
    return get_or_create_conversation(call_sid)["complete"]


def end_conversation(call_sid: str):
    """Nettoie la mémoire une fois l'appel terminé et le résumé envoyé."""
    _conversations.pop(call_sid, None)