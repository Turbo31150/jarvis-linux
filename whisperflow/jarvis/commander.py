"""
JARVIS Commander - Parseur et dispatcher de commandes vocales
Analyse le texte transcrit et route vers le bon skill/agent
"""

import re
import logging
import asyncio
from typing import Optional, Callable, Awaitable

logger = logging.getLogger("jarvis.commander")


class CommandResult:
    """Résultat d'une commande exécutée"""
    def __init__(self, success: bool, message: str = "", data=None):
        self.success = success
        self.message = message
        self.data = data


class VoiceCommand:
    """Représentation d'une commande vocale parsée"""
    def __init__(self, raw_text: str, intent: str, target: str = "",
                 params: dict = None, confidence: float = 1.0):
        self.raw_text = raw_text
        self.intent = intent
        self.target = target
        self.params = params or {}
        self.confidence = confidence

    def __repr__(self):
        return f"VoiceCommand(intent='{self.intent}', target='{self.target}')"


# Patterns de commandes vocales FR/EN
# ORDRE CRITIQUE: patterns spécifiques AVANT patterns génériques
COMMAND_PATTERNS = [
    # === DICTÉE (prioritaire - avant app_close qui matche "arrête") ===
    (r"(?:mode\s+dictée|dictation\s+mode|commence\s+à\s+écrire|écris)",
     "dictation_start"),
    (r"(?:arrête\s+la\s+dictée|stop\s+dictation|fin\s+de\s+dictée|arrête\s+d'écrire)",
     "dictation_stop"),
    (r"(?:nouvelle\s+ligne|new\s+line|à\s+la\s+ligne|retour\s+à\s+la\s+ligne)",
     "dictation_newline"),
    (r"(?:\bpoint\s+final\b|\bpoint\s*$)",
     "dictation_period"),

    # === BUREAUX VIRTUELS (avant média car "suivant/précédent" conflicte) ===
    (r"(?:nouveau\s+bureau\s+virtuel|new\s+desktop|cr[ée]+\s+un\s+bureau)",
     "vdesktop_new"),
    (r"(?:ferme\s+(?:le\s+)?bureau\s+virtuel|close\s+desktop)",
     "vdesktop_close"),
    (r"(?:bureau\s+virtuel\s+(?:pr[ée]c[ée]dent|gauche)|desktop\s+left)",
     "vdesktop_left"),
    (r"(?:bureau\s+virtuel\s+(?:suivant|droite)|desktop\s+right)",
     "vdesktop_right"),
    (r"(?:vue\s+des?\s+t[âa]ches|task\s+view)",
     "vdesktop_task_view"),

    # === MÉDIA (avant app_close car "arrête la musique" conflicte) ===
    (r"(?:arrête\s+la\s+musique|arrête\s+la\s+lecture)",
     "media_pause"),
    (r"(?:play|lecture|joue|jouer)",
     "media_play"),
    (r"(?:pause)",
     "media_pause"),
    (r"(?:suivant|next|piste\s+suivante|chanson\s+suivante)",
     "media_next"),
    (r"(?:\bprécédent\b|previous|piste\s+précédente|chanson\s+précédente)",
     "media_previous"),

    # === PROCESSUS & MONITORING (avant app_launch car "liste/kill" conflicte) ===
    (r"(?:liste|lister|list)\s+(?:les\s+)?(?:processus|process|tâches)",
     "process_list"),
    (r"(?:tue|tuer|kill)\s+(?:le\s+)?(?:processus|process)\s+(.+)",
     "process_kill"),
    (r"(?:ressources|resources|\bcharge\b|utilisation)\s*(?:système|system)?",
     "system_resources"),
    (r"(?:utilisation\s+(?:cpu|ram|système|system))",
     "system_resources"),
    (r"(?:cpu|processeur)\s*(?:usage|utilisation)?",
     "system_top_cpu"),
    (r"(?:\bram\b|mémoire|memory)\s*(?:usage|utilisation)?",
     "system_resources"),
    (r"(?:espace\s+disque|disk\s+space|stockage|disque\s+dur)",
     "system_disk"),
    (r"(?:uptime|durée\s+de\s+fonctionnement|allumé\s+depuis)",
     "system_uptime"),
    (r"(?:gpu|carte\s+graphique)",
     "system_gpu"),
    (r"(?:matériel|hardware|specs|configuration\s+matérielle|info(?:rmation)?s?\s+(?:matériel(?:les?)?|système)|system\s+info)",
     "system_hardware"),

    # === RÉSEAU (avant app_launch) ===
    (r"(?:état\s+(?:du\s+)?réseau|network\s+status|interfaces?\s+réseau)",
     "network_status"),
    (r"(?:(?:adresse\s+)?ip\s+publique|public\s+ip|ip\s+externe)",
     "network_ip_public"),
    (r"(?:adresse\s+ip|ip\s+locale|mon\s+ip|ip\s+address)",
     "network_ip"),
    (r"(?:ping)\s+(.+)",
     "network_ping"),
    (r"(?:teste?\s+(?:la\s+)?connexion|connection\s+test)",
     "network_ping"),
    (r"(?:réseaux?\s+wifi|wifi\s+(?:disponibles?|list)|scan\s+wifi)",
     "network_wifi_list"),
    (r"(?:test\s+(?:de\s+)?débit|speed\s*test|vitesse\s+internet)",
     "network_speed"),

    # === ALIMENTATION & AFFICHAGE (avant jarvis_settings car "paramètres" conflicte) ===
    (r"(?:plan\s+(?:d')?alimentation|power\s+plan)",
     "power_plan"),
    (r"(?:haute\s+performance|high\s+performance|mode\s+performance)",
     "power_high_perf"),
    (r"(?:mode\s+équilibré|balanced)",
     "power_balanced"),
    (r"(?:économie\s+d'énergie|power\s+saver|mode\s+éco)",
     "power_saver"),
    (r"(?:hibernation|hiberne|hibernate)",
     "power_hibernate"),
    (r"(?:résolution)\s*(?:d'écran)?",
     "display_resolution"),
    (r"(?:mode\s+nuit|night\s+(?:mode|light)|lumière\s+bleue|filtre\s+bleu)",
     "display_night"),
    (r"(?:paramètres?\s+(?:d')?affichage|display\s+settings)",
     "display_settings"),
    (r"(?:paramètres?\s+(?:du?\s+)?son|audio\s+settings|paramètres?\s+audio)",
     "audio_settings"),

    # === LOGICIELS winget (avant app_launch car "installe/désinstalle" conflicte) ===
    (r"(?:désinstalle|désinstaller|uninstall)\s+(?:le\s+)?(?:logiciel|programme)?\s*(.+)",
     "software_uninstall"),
    (r"(?:installe|installer|install)\s+(?:le\s+)?(?:logiciel|programme|package)?\s*(.+)",
     "software_install"),
    (r"(?:mets?\s+à\s+jour\s+tout|update\s+all|mise\s+à\s+jour\s+(?:de\s+)?tout)",
     "software_update_all"),
    (r"(?:liste\s+(?:les\s+)?(?:logiciels|programmes)|installed\s+software|programmes?\s+installés?)",
     "software_list"),
    (r"(?:mises?\s+à\s+jour|updates?\s+disponibles?|vérifi(?:e|er)\s+(?:les\s+)?mises?\s+à\s+jour)",
     "software_check_updates"),

    # === PRESSE-PAPIERS (avant app_launch) ===
    (r"(?:lis\s+le\s+presse-papiers|read\s+clipboard|contenu\s+(?:du\s+)?presse-papiers)",
     "clipboard_read"),
    (r"(?:coupe\s+le\s+son)",
     "system_mute"),
    (r"(?:coupe|couper|\bcut\b)\s*(?:la\s+)?(?:sélection)?",
     "clipboard_cut"),
    (r"(?:sélectionne\s+tout|select\s+all|tout\s+sélectionner)",
     "clipboard_select_all"),

    # === NAVIGATION DOSSIERS (avant app_launch car "ouvre" conflicte) ===
    (r"(?:ouvre|ouvrir)\s+(?:le\s+)?(?:dossier|répertoire|folder)\s+(.+)",
     "navigate_folder"),
    (r"(?:ouvre|ouvrir)\s+(?:les\s+)?(?:t[ée]l[ée]chargements|downloads)",
     "navigate_downloads"),
    (r"(?:ouvre|ouvrir)\s+(?:les\s+)?(?:documents)",
     "navigate_documents"),
    (r"(?:ouvre|ouvrir)\s+(?:le\s+)?(?:bureau|desktop)",
     "navigate_desktop"),

    # === WEB (avant fichiers car "recherche sur google" conflicte avec file_search) ===
    (r"(?:google|recherche\s+sur\s+google|cherche\s+sur\s+google)\s+(.+)",
     "web_google"),
    (r"(?:youtube)\s+(.+)",
     "web_youtube"),
    (r"(?:wikipedia|wiki)\s+(.+)",
     "web_wikipedia"),
    (r"(?:va\s+sur|ouvre\s+le\s+site|navigate|go\s+to)\s+(.+)",
     "web_navigate"),
    (r"(?:météo|weather|temps\s+qu'il\s+fait)",
     "web_weather"),

    # === NAVIGATION AVANCEE (browser memory + landmarks) ===
    (r"(?:ajoute\s+(?:aux?|en)\s+favoris|bookmark|sauvegarde\s+cette\s+page|enregistre\s+cette\s+page|mets?\s+en\s+favori|garde\s+cette\s+page)",
     "browser_bookmark"),
    (r"(?:liste\s+(?:les\s+|mes\s+)?favoris|mes\s+bookmarks|montre\s+les\s+favoris|mes\s+pages\s+sauvegard[ée]es)",
     "browser_bookmarks_list"),
    (r"(?:historique\s+(?:de\s+)?navigation|pages?\s+r[ée]centes?|derni[èe]res?\s+pages?\s+visit[ée]es?)",
     "browser_history"),
    (r"(?:cherche\s+dans\s+l[' ]?historique|retrouve\s+la\s+page|trouve\s+la\s+page\s+sur|o[ùu]\s+j'?ai\s+vu)\s+(.+)",
     "browser_search_history"),
    (r"(?:retourne\s+sur|r[ée]ouvre|reviens?\s+sur)\s+(.+)",
     "browser_goto_remembered"),
    (r"(?:rep[èe]res?\s+(?:de\s+)?la\s+page|structure\s+de\s+la\s+page|analyse\s+la\s+page|qu'est-ce\s+qu'il\s+y\s+a\s+sur\s+la\s+page|lis?\s+les\s+titres|montre\s+les\s+[ée]l[ée]ments)",
     "browser_landmarks"),
    (r"(?:va\s+au|descends?\s+jusqu'[àa]|trouve\s+sur\s+la\s+page|scroll\s+vers|montre[\s-]moi)\s+(.+)",
     "browser_scroll_to"),
    (r"(?:r[ée]sume\s+cette\s+page|c'est\s+quoi\s+cette\s+page|de\s+quoi\s+parle\s+cette\s+page|r[ée]sume\s+le\s+contenu|explique\s+cette\s+page)",
     "browser_summarize"),
    (r"(?:note\s+sur\s+cette\s+page|ajoute\s+la\s+note|prends?\s+note|rappelle?\s+que)\s+(.+)",
     "browser_add_note"),
    (r"(?:sauvegarde\s+(?:les\s+)?onglets|sauvegarde\s+la\s+session|enregistre\s+les\s+onglets)\s*(?:sous\s+)?(.+)?",
     "browser_save_session"),
    (r"(?:restaure\s+la\s+session|ouvre\s+la\s+session|charge\s+la\s+session|recharge\s+les\s+onglets)\s+(.+)",
     "browser_restore_session"),
    (r"(?:pages?\s+les?\s+plus\s+visit[ée](?:e?s)?|mes?\s+sites?\s+pr[ée]f[ée]r[ée](?:e?s)?|top\s+pages?)",
     "browser_most_visited"),
    (r"(?:lis\s+la\s+page|qu'est-ce\s+qui\s+est\s+[ée]crit|lis\s+le\s+contenu)",
     "browser_read"),
    (r"(?:clique\s+sur|appuie\s+sur)\s+(.+)",
     "browser_click"),

    # === MINUTEUR & RAPPELS (avant app_launch) ===
    (r"(?:minuteur|timer|chrono(?:m[èe]tre)?)\s+(.+)",
     "timer_set"),
    (r"(?:rappelle[\s-]moi|reminder|rappel)\s+(?:dans\s+)?(.+)",
     "timer_reminder"),
    (r"(?:annule|cancel)\s+(?:le\s+)?(?:minuteur|timer|chrono|rappel)",
     "timer_cancel"),
    (r"(?:liste\s+(?:les\s+)?(?:minuteurs|timers|rappels)|timers?\s+actifs?)",
     "timer_list"),

    # === NOTES RAPIDES ===
    (r"(?:note|noter|prends?\s+(?:en\s+)?note)\s+(.+)",
     "note_add"),
    (r"(?:lis|lire)\s+(?:les\s+)?notes",
     "note_read"),
    (r"(?:efface|supprime|clear)\s+(?:les\s+)?notes",
     "note_clear"),
    (r"(?:cherche|search)\s+(?:dans\s+)?(?:les\s+)?notes\s+(.+)",
     "note_search"),

    # === CONVERSION D'UNITES (avant calc_convert car "convertis X en Y" conflicte) ===
    (r"(?:convertis?|conversion?|convert)\s+(\d+(?:[.,]\d+)?)\s*([a-zéèêàâôûïü-]+)\s+(?:en|to|vers)\s+([a-zéèêàâôûïü-]+)",
     "unit_convert"),

    # === CALCULATRICE ===
    (r"(?:calcule|calculer|calculate|combien\s+fait)\s+(.+)",
     "calc_compute"),
    (r"(\d+)\s*(?:pourcent|%|percent)\s+(?:de|of)\s+(\d+)",
     "calc_percentage"),
    (r"(?:convertis?|conversion?|convert)\s+(.+)",
     "calc_convert"),

    # === TRADUCTION (avant app_launch) ===
    (r"(?:traduis?|traduire|translate)\s+en\s+anglais\s+(.+)",
     "translate_fr_en"),
    (r"(?:traduis?|traduire|translate)\s+en\s+fran[çc]ais\s+(.+)",
     "translate_en_fr"),
    (r"(?:traduis?|traduire|translate)\s+(.+)\s+en\s+anglais",
     "translate_fr_en"),
    (r"(?:traduis?|traduire|translate)\s+(.+)\s+en\s+fran[çc]ais",
     "translate_en_fr"),
    (r"(?:traduction|translation)\s+(?:de\s+)?(.+)",
     "translate_lookup"),

    # === POMODORO (stop/status AVANT start car "pomodoro" nu dans start matche tout) ===
    (r"(?:arr[êe]te\s+(?:le\s+)?pomodoro|stop\s+pomodoro|fin\s+(?:du\s+)?pomodoro)",
     "pomodoro_stop"),
    (r"(?:[ée]tat\s+(?:du\s+)?pomodoro|pomodoro\s+status|o[ùu]\s+en\s+est\s+le\s+pomodoro|status\s+pomodoro)",
     "pomodoro_status"),
    (r"(?:pomodoro|lance\s+(?:un\s+)?pomodoro|technique\s+pomodoro|mode\s+travail)",
     "pomodoro_start"),

    # === SNAPSHOT SYSTEME ===
    (r"(?:snapshot\s+(?:du\s+)?syst[èe]me|capture\s+(?:du\s+)?syst[èe]me|[ée]tat\s+complet|system\s+snapshot|bilan\s+syst[èe]me)",
     "snapshot_take"),
    (r"(?:compare\s+(?:les\s+)?snapshots?|comparaison\s+syst[èe]me|diff\s+syst[èe]me)",
     "snapshot_compare"),
    (r"(?:historique\s+(?:des\s+)?snapshots?|snapshots?\s+pr[ée]c[ée]dents?)",
     "snapshot_history"),

    # === MOT DE PASSE ===
    (r"(?:g[ée]n[èe]re|g[ée]n[ée]rer|generate)\s+(?:un\s+)?(?:mot\s+de\s+passe|password|mdp)\s*(.*)",
     "password_generate"),
    (r"(?:force|strength)\s+(?:du\s+)?(?:mot\s+de\s+passe|password)\s+(.+)",
     "password_strength"),

    # === DATES (avant app_launch car "dans combien" conflicte) ===
    (r"(?:dans\s+combien\s+de\s+jours?|combien\s+de\s+jours?\s+(?:avant|jusqu'[àa]))\s+(.+)",
     "date_days_until"),
    (r"(?:quel\s+jour)\s+(?:sera|serons-nous|dans)\s+(.+)",
     "date_add_days"),
    (r"(?:dans\s+(\d+)\s+jours?)",
     "date_add_days"),
    (r"(?:quel\s+jour\s+(?:[ée]tait|est)\s+le|jour\s+de\s+la\s+semaine)\s+(.+)",
     "date_day_of_week"),

    # === OUTILS TEXTE ===
    (r"(?:compte\s+(?:les\s+)?mots?|word\s+count)\s+(?:dans\s+|de\s+)?(.+)",
     "text_count"),
    (r"(?:en\s+majuscules?|uppercase|majuscule)\s+(.+)",
     "text_uppercase"),
    (r"(?:en\s+minuscules?|lowercase|minuscule)\s+(.+)",
     "text_lowercase"),
    (r"(?:acronyme|acronym)\s+(?:de\s+)?(.+)",
     "text_acronym"),
    (r"(?:[ée]pelle|[ée]peler|spell)\s+(.+)",
     "text_spell"),

    # === FAVORIS (avant app_launch car "ajoute/lance favori" conflicte) ===
    (r"(?:ajoute\s+(?:en|aux?)\s+favoris?|favori\s+ajout(?:e|er))\s+(.+)",
     "fav_add"),
    (r"(?:liste\s+(?:les\s+)?favoris?|mes\s+favoris?|favoris?\s+list)",
     "fav_list"),
    (r"(?:supprime\s+(?:le\s+)?favori|retire\s+(?:le\s+)?favori|favori\s+supprim(?:e|er))\s+(.+)",
     "fav_remove"),
    (r"(?:lance\s+(?:le\s+)?favori|favori)\s+(\d+|.+)",
     "fav_run"),

    # === CHRONOMETRE ===
    (r"(?:chrono(?:m[èe]tre)?\s+(?:d[ée]marre|start|lance)|d[ée]marre\s+(?:le\s+)?chrono(?:m[èe]tre)?|start\s+stopwatch)",
     "stopwatch_start"),
    (r"(?:arr[êe]te\s+(?:le\s+)?chrono(?:m[èe]tre)?|stop\s+(?:le\s+)?chrono(?:m[èe]tre)?|chrono\s+stop)",
     "stopwatch_stop"),
    (r"(?:tour|lap)\s*(?:du\s+)?(?:chrono(?:m[èe]tre)?)?",
     "stopwatch_lap"),
    (r"(?:r[ée]initialise|reset)\s+(?:le\s+)?chrono(?:m[èe]tre)?",
     "stopwatch_reset"),
    (r"(?:temps\s+(?:du\s+)?chrono(?:m[èe]tre)?|chrono\s+status)",
     "stopwatch_status"),

    # === AGENDA (clear/next AVANT list car "l'agenda" dans list matche trop) ===
    (r"(?:agenda\s+ajoute|ajoute\s+(?:[àa])\s+l'agenda|[ée]v[ée]nement)\s+(.+)",
     "agenda_add"),
    (r"(?:vide\s+(?:l')?agenda|efface\s+(?:l')?agenda|clear\s+agenda)",
     "agenda_clear"),
    (r"(?:prochain\s+[ée]v[ée]nement|next\s+event|qu'est-ce\s+(?:que\s+)?(?:j'ai\s+)?(?:apr[èe]s|ensuite))",
     "agenda_next"),
    (r"(?:agenda|(?:mon|l')\s*agenda|planning|[ée]v[ée]nements?\s+(?:du\s+jour|pr[ée]vus?))",
     "agenda_list"),

    # === ALEATOIRE ===
    (r"(?:pile\s+ou\s+face|coin\s+flip|lance\s+(?:une\s+)?pi[èe]ce)",
     "random_coin"),
    (r"(?:lance\s+(?:un\s+)?d[ée]|d[ée]\s+[àa]\s+(\d+)|roll\s+dice|jet\s+de\s+d[ée])",
     "random_dice"),
    (r"(?:choisis?\s+(?:entre|parmi)|pick|random\s+choice)\s+(.+)",
     "random_pick"),
    (r"(?:nombre\s+al[ée]atoire|random\s+number|nombre\s+au\s+hasard)\s*(.*)",
     "random_number"),

    # === ABREVIATIONS (list avant define car "abreviations" matche aussi define) ===
    (r"(?:liste\s+(?:des?\s+)?abr[ée]viations?|abr[ée]viations?\s+(?:disponibles?|connues?))",
     "abbrev_list"),
    (r"(?:(?:que\s+)?(?:signifie|veut\s+dire)|d[ée]finition\s+(?:de\s+)?|abr[ée]viation)\s*([A-Za-zÀ-ÿ]+)",
     "abbrev_define"),

    # === AUTOMATISATION (avant app_launch car "lance macro" conflicte) ===
    (r"(?:exécute|exécuter|run|lance)\s+(?:l[ea]\s+)?(?:macro|automatisation|script)\s+(.+)",
     "automation_run"),
    (r"(?:automatise|automatiser|automate|macro)\s+(.+)",
     "automation_create"),

    # === APPLICATIONS (générique - après tous les patterns spécifiques) ===
    (r"(?:ouvre|ouvrir|lance|lancer|démarre|démarrer|start|open|launch)\s+(.+)",
     "app_launch"),
    (r"(?:ferme|fermer|quitte|quitter|close|kill|arrête|arrêter)\s+(.+)",
     "app_close"),

    # === FICHIERS ===
    (r"(?:crée|créer|nouveau|nouvelle)\s+(?:un\s+)?(?:fichier|dossier|répertoire)\s+(.+)",
     "file_create"),
    (r"(?:supprime|supprimer|efface|effacer|delete)\s+(?:le\s+)?(?:fichier|dossier)?\s*(.+)",
     "file_delete"),
    (r"(?:cherche|chercher|recherche(?:r)?|trouve|trouver|find|search)\s+(?:le\s+fichier\s+)?(.+)",
     "file_search"),
    (r"(?:renomme|renommer|rename)\s+(.+)\s+en\s+(.+)",
     "file_rename"),
    (r"(?:copie|copier|copy)\s+(.+)",
     "clipboard_copy"),
    (r"(?:colle|coller|paste)",
     "clipboard_paste"),

    # === FENÊTRES ===
    (r"(?:minimise|minimiser|minimize)\s*(?:la\s+)?(?:fenêtre)?",
     "window_minimize"),
    (r"(?:maximise|maximiser|maximize)\s*(?:la\s+)?(?:fenêtre)?",
     "window_maximize"),
    (r"(?:restaure|restaurer|restore)\s*(?:la\s+)?(?:fenêtre)?",
     "window_restore"),
    (r"(?:bascule|basculer|switch|alt.?tab)",
     "window_switch"),
    (r"(?:bureau|show\s+desktop|affiche\s+le\s+bureau)",
     "window_desktop"),
    (r"(?:capture|screenshot|écran)\s*(?:d'écran)?",
     "window_screenshot"),

    # === SYSTÈME ===
    (r"(?:volume)\s+(?:à|a|au)?\s*(\d+)",
     "system_volume_set"),
    (r"(?:monte|augmente|plus\s+fort|volume\s+up|up\s+volume)\s*(?:le\s+)?(?:volume|son)?",
     "system_volume_up"),
    (r"(?:baisse|diminue|moins\s+fort|volume\s+down|down\s+volume)\s*(?:le\s+)?(?:volume|son)?",
     "system_volume_down"),
    (r"(?:muet|mute|coupe\s+le\s+son|silence)",
     "system_mute"),
    (r"(?:luminosité|brightness)\s+(?:à|a|au)?\s*(\d+)",
     "system_brightness"),
    (r"(?:wifi)\s+(on|off|active|désactive)",
     "system_wifi"),
    (r"(?:bluetooth)\s+(on|off|active|désactive)",
     "system_bluetooth"),
    (r"(?:éteins|éteindre|shutdown|arrête\s+l'ordinateur)",
     "system_shutdown"),
    (r"(?:redémarre|redémarrer|restart|reboot)",
     "system_restart"),
    (r"(?:veille|sleep|mise\s+en\s+veille|verrouille|lock)",
     "system_sleep"),
    (r"(?:batterie|battery|autonomie)",
     "system_battery"),
    (r"(?:heure|quelle\s+heure|time)",
     "system_time"),
    (r"(?:date|quel\s+jour|today)",
     "system_date"),

    # === CONTRÔLE JARVIS ===
    (r"(?:aide|help|qu'est-ce\s+que\s+tu\s+(?:sais|peux)\s+faire|commandes)",
     "jarvis_help"),
    (r"(?:statut|status|état|state)",
     "jarvis_status"),
    (r"(?:au\s+revoir|goodbye|bye|à\s+plus|bonne\s+nuit|stop\s+jarvis|quitte\s+jarvis)",
     "jarvis_quit"),
    (r"(?:merci|thanks|thank\s+you)",
     "jarvis_thanks"),
    (r"(?:répète|repeat|redis)",
     "jarvis_repeat"),
    (r"(?:annule|cancel|undo|annuler)",
     "jarvis_cancel"),
    (r"(?:paramètres|settings|configuration|config)\s*(?:de\s+)?(?:jarvis)?",
     "jarvis_settings"),
]


def _normalize_accents(text: str) -> str:
    """Normalise les accents pour matcher Whisper output (souvent sans accents)."""
    # Add accented variants so both 'dictee' and 'dictée' match
    import unicodedata
    # Decompose then remove combining chars → pure ASCII
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


class Commander:
    """Parseur et dispatcher principal de commandes vocales"""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._last_command: Optional[VoiceCommand] = None
        # Compile patterns with both accented and normalized versions
        self._compiled_patterns = []
        for pattern, intent in COMMAND_PATTERNS:
            self._compiled_patterns.append(
                (re.compile(pattern, re.IGNORECASE), intent)
            )
            # Also compile accent-stripped version
            stripped = _normalize_accents(pattern)
            if stripped != pattern:
                self._compiled_patterns.append(
                    (re.compile(stripped, re.IGNORECASE), intent)
                )

    def register(self, intent: str, handler: Callable[..., Awaitable[CommandResult]]):
        """Enregistre un handler pour un intent donné"""
        self._handlers[intent] = handler
        logger.debug(f"Handler enregistré: {intent}")

    def parse(self, text: str) -> Optional[VoiceCommand]:
        """Parse le texte en une commande vocale structurée"""
        if not text or not text.strip():
            return None

        text_clean = text.strip().lower()
        # Also try accent-stripped version of the input
        text_normalized = _normalize_accents(text_clean)

        for pattern, intent in self._compiled_patterns:
            match = pattern.search(text_clean) or pattern.search(text_normalized)
            if match:
                groups = match.groups()
                target = groups[0].strip() if groups and groups[0] else ""
                params = {"groups": groups} if len(groups) > 1 else {}

                cmd = VoiceCommand(
                    raw_text=text,
                    intent=intent,
                    target=target,
                    params=params,
                    confidence=0.9
                )
                logger.info(f"Commande parsée: {cmd}")
                return cmd

        return VoiceCommand(
            raw_text=text,
            intent="unknown",
            target=text_clean,
            confidence=0.3
        )

    async def execute(self, command: VoiceCommand) -> CommandResult:
        """Exécute une commande vocale via le handler approprié"""
        self._last_command = command

        handler = self._handlers.get(command.intent)
        if handler:
            try:
                logger.info(f"Exécution: {command.intent} -> {command.target}")
                return await handler(command)
            except Exception as e:
                logger.error(f"Erreur exécution {command.intent}: {e}")
                return CommandResult(False, f"Erreur: {e}")

        logger.warning(f"Aucun handler pour intent: {command.intent}")
        return CommandResult(False, "Commande non reconnue")

    async def process_text(self, text: str) -> CommandResult:
        """Pipeline complet: parse + execute"""
        command = self.parse(text)
        if command is None:
            return CommandResult(False, "Texte vide")
        return await self.execute(command)

    @property
    def last_command(self) -> Optional[VoiceCommand]:
        return self._last_command

    def list_intents(self) -> list:
        """Liste tous les intents enregistrés"""
        return list(self._handlers.keys())
