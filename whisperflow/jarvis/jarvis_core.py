"""
JARVIS Core - Orchestrateur principal
Connecte Whisper-Flow (STT) + Commander + Skills + Agents + TTS
"""

import asyncio
import logging
from typing import Optional

from .commander import Commander, CommandResult, VoiceCommand
from .wake_word import detect_wake_word
from .tts_engine import TTSEngine
from .config import config

# Skills
from .skills.app_launcher import AppLauncherSkill
from .skills.system_control import SystemControlSkill
from .skills.window_manager import WindowManagerSkill
from .skills.file_manager import FileManagerSkill
from .skills.web_browser import WebBrowserSkill
from .skills.media_control import MediaControlSkill
from .skills.clipboard_manager import ClipboardManagerSkill
from .skills.process_manager import ProcessManagerSkill
from .skills.network_control import NetworkControlSkill
from .skills.power_display import PowerDisplaySkill
from .skills.software_manager import SoftwareManagerSkill
from .skills.timer_reminder import TimerReminderSkill
from .skills.quick_notes import QuickNotesSkill
from .skills.calculator import CalculatorSkill
from .skills.virtual_desktop import VirtualDesktopSkill
from .skills.translator import TranslatorSkill
from .skills.unit_converter import UnitConverterSkill
from .skills.pomodoro import PomodoroSkill
from .skills.system_snapshot import SystemSnapshotSkill
from .skills.password_generator import PasswordGeneratorSkill
from .skills.date_calculator import DateCalculatorSkill
from .skills.text_tools import TextToolsSkill
from .skills.favorites import FavoritesSkill
from .skills.stopwatch import StopwatchSkill
from .skills.agenda import AgendaSkill
from .skills.random_picker import RandomPickerSkill
from .skills.abbreviations import AbbreviationsSkill

# Agents
from .agents.dictation_agent import DictationAgent
from .agents.search_agent import SearchAgent
from .agents.automation_agent import AutomationAgent
from .agents.navigation_agent import NavigationAgent
from .cluster_bridge import cluster_race, query_m1, dispatch_cowork

logger = logging.getLogger("jarvis.core")


class Jarvis:
    """JARVIS - Just A Rather Very Intelligent System"""

    def __init__(self):
        self.commander = Commander()
        self.tts = TTSEngine(
            voice=config.get("tts_voice", "fr-FR-HenriNeural"),
            rate=config.get("tts_rate", "+10%")
        )

        # Skills
        self.app_launcher = AppLauncherSkill()
        self.system_control = SystemControlSkill()
        self.window_manager = WindowManagerSkill()
        self.file_manager = FileManagerSkill()
        self.web_browser = WebBrowserSkill()
        self.media_control = MediaControlSkill()
        self.clipboard = ClipboardManagerSkill()
        self.process_mgr = ProcessManagerSkill()
        self.network = NetworkControlSkill()
        self.power_display = PowerDisplaySkill()
        self.software = SoftwareManagerSkill()
        self.timer = TimerReminderSkill()
        self.notes = QuickNotesSkill()
        self.calculator = CalculatorSkill()
        self.vdesktop = VirtualDesktopSkill()
        self.translator = TranslatorSkill()
        self.unit_converter = UnitConverterSkill()
        self.pomodoro = PomodoroSkill()
        self.snapshot = SystemSnapshotSkill()
        self.password = PasswordGeneratorSkill()
        self.date_calc = DateCalculatorSkill()
        self.text_tools = TextToolsSkill()
        self.favorites = FavoritesSkill()
        self.stopwatch = StopwatchSkill()
        self.agenda = AgendaSkill()
        self.random_picker = RandomPickerSkill()
        self.abbreviations = AbbreviationsSkill()

        # Agents
        self.dictation = DictationAgent()
        self.search = SearchAgent()
        self.automation = AutomationAgent()
        self.navigation = NavigationAgent()

        # State
        self._pending_action = None
        self._running = False

        self._register_all_handlers()

    def _register_all_handlers(self):
        """Enregistre tous les handlers de commandes"""
        c = self.commander

        # Applications
        c.register("app_launch", self.app_launcher.launch)
        c.register("app_close", self.app_launcher.close)

        # Système
        c.register("system_volume_set", self.system_control.volume_set)
        c.register("system_volume_up", self.system_control.volume_up)
        c.register("system_volume_down", self.system_control.volume_down)
        c.register("system_mute", self.system_control.mute)
        c.register("system_brightness", self.system_control.brightness)
        c.register("system_wifi", self.system_control.wifi)
        c.register("system_bluetooth", self.system_control.bluetooth)
        c.register("system_shutdown", self.system_control.shutdown)
        c.register("system_restart", self.system_control.restart)
        c.register("system_sleep", self.system_control.sleep)
        c.register("system_battery", self.system_control.battery)
        c.register("system_time", self.system_control.time)
        c.register("system_date", self.system_control.date)

        # Fenêtres
        c.register("window_minimize", self.window_manager.minimize)
        c.register("window_maximize", self.window_manager.maximize)
        c.register("window_restore", self.window_manager.restore)
        c.register("window_switch", self.window_manager.switch)
        c.register("window_desktop", self.window_manager.desktop)
        c.register("window_screenshot", self.window_manager.screenshot)

        # Fichiers
        c.register("file_create", self.file_manager.create)
        c.register("file_delete", self.file_manager.delete)
        c.register("file_search", self.file_manager.search)
        c.register("file_rename", self.file_manager.rename)

        # Web
        c.register("web_google", self.web_browser.google)
        c.register("web_youtube", self.web_browser.youtube)
        c.register("web_wikipedia", self.web_browser.wikipedia)
        c.register("web_navigate", self.web_browser.navigate)
        c.register("web_weather", self.web_browser.weather)

        # Média
        c.register("media_play", self.media_control.play)
        c.register("media_pause", self.media_control.pause)
        c.register("media_next", self.media_control.next_track)
        c.register("media_previous", self.media_control.previous_track)

        # Presse-papiers
        c.register("clipboard_copy", self.clipboard.copy)
        c.register("clipboard_paste", self.clipboard.paste)
        c.register("clipboard_cut", self.clipboard.cut)
        c.register("clipboard_select_all", self.clipboard.select_all)
        c.register("clipboard_read", self.clipboard.read_clipboard)

        # Processus & Monitoring
        c.register("process_list", self.process_mgr.list_processes)
        c.register("process_kill", self.process_mgr.kill_process)
        c.register("system_resources", self.process_mgr.system_resources)
        c.register("system_top_cpu", self.process_mgr.top_cpu)
        c.register("system_disk", self.process_mgr.disk_space)
        c.register("system_uptime", self.process_mgr.uptime)
        c.register("system_gpu", self.process_mgr.gpu_info)
        c.register("system_hardware", self.process_mgr.hardware_info)

        # Réseau
        c.register("network_status", self.network.network_status)
        c.register("network_ip", self.network.ip_local)
        c.register("network_ip_public", self.network.ip_public)
        c.register("network_ping", self.network.ping)
        c.register("network_wifi_list", self.network.wifi_list)
        c.register("network_speed", self.network.speed_test)

        # Alimentation & Affichage
        c.register("power_plan", self.power_display.power_plan)
        c.register("power_high_perf", self.power_display.set_high_performance)
        c.register("power_balanced", self.power_display.set_balanced)
        c.register("power_saver", self.power_display.set_power_saver)
        c.register("power_hibernate", self.power_display.hibernate)
        c.register("display_resolution", self.power_display.screen_resolution)
        c.register("display_night", self.power_display.night_mode)
        c.register("display_settings", self.power_display.display_settings)
        c.register("audio_settings", self.power_display.sound_settings)

        # Logiciels
        c.register("software_install", self.software.install)
        c.register("software_uninstall", self.software.uninstall)
        c.register("software_update_all", self.software.update_all)
        c.register("software_list", self.software.list_installed)
        c.register("software_check_updates", self.software.check_updates)

        # Navigation dossiers
        c.register("navigate_folder", self.navigation.navigate)
        c.register("navigate_downloads", self._nav_downloads)
        c.register("navigate_documents", self._nav_documents)
        c.register("navigate_desktop", self._nav_desktop)

        # Dictée
        c.register("dictation_start", self.dictation.start)
        c.register("dictation_stop", self.dictation.stop)
        c.register("dictation_newline", self.dictation.newline)
        c.register("dictation_period", self.dictation.period)

        # Minuteurs & Rappels
        c.register("timer_set", self.timer.set_timer)
        c.register("timer_reminder", self.timer.set_reminder)
        c.register("timer_cancel", self.timer.cancel_timer)
        c.register("timer_list", self.timer.list_timers)

        # Notes rapides
        c.register("note_add", self.notes.add_note)
        c.register("note_read", self.notes.read_notes)
        c.register("note_clear", self.notes.clear_notes)
        c.register("note_search", self.notes.search_notes)

        # Calculatrice
        c.register("calc_compute", self.calculator.calculate)
        c.register("calc_percentage", self.calculator.percentage)
        c.register("calc_convert", self.calculator.convert_temperature)

        # Bureaux virtuels
        c.register("vdesktop_new", self.vdesktop.new_desktop)
        c.register("vdesktop_close", self.vdesktop.close_desktop)
        c.register("vdesktop_left", self.vdesktop.switch_left)
        c.register("vdesktop_right", self.vdesktop.switch_right)
        c.register("vdesktop_task_view", self.vdesktop.task_view)

        # Traduction
        c.register("translate_fr_en", self.translator.translate_fr_en)
        c.register("translate_en_fr", self.translator.translate_en_fr)
        c.register("translate_lookup", self.translator.lookup)

        # Conversion d'unités
        c.register("unit_convert", self.unit_converter.convert)

        # Pomodoro
        c.register("pomodoro_start", self.pomodoro.start)
        c.register("pomodoro_stop", self.pomodoro.stop)
        c.register("pomodoro_status", self.pomodoro.status)

        # Snapshot système
        c.register("snapshot_take", self.snapshot.take_snapshot)
        c.register("snapshot_compare", self.snapshot.compare)
        c.register("snapshot_history", self.snapshot.history)

        # Mot de passe
        c.register("password_generate", self.password.generate)
        c.register("password_strength", self.password.strength)

        # Dates
        c.register("date_days_until", self.date_calc.days_until)
        c.register("date_add_days", self.date_calc.add_days_cmd)
        c.register("date_day_of_week", self.date_calc.day_of_week)

        # Outils texte
        c.register("text_count", self.text_tools.count_words)
        c.register("text_uppercase", self.text_tools.uppercase)
        c.register("text_lowercase", self.text_tools.lowercase)
        c.register("text_acronym", self.text_tools.acronym)
        c.register("text_spell", self.text_tools.spell)

        # Favoris
        c.register("fav_add", self.favorites.add)
        c.register("fav_list", self.favorites.list_favorites)
        c.register("fav_remove", self.favorites.remove)
        c.register("fav_run", self.favorites.run_favorite)

        # Chronometre
        c.register("stopwatch_start", self.stopwatch.start)
        c.register("stopwatch_stop", self.stopwatch.stop)
        c.register("stopwatch_lap", self.stopwatch.lap)
        c.register("stopwatch_reset", self.stopwatch.reset)
        c.register("stopwatch_status", self.stopwatch.status)

        # Agenda
        c.register("agenda_add", self.agenda.add_event)
        c.register("agenda_list", self.agenda.list_events)
        c.register("agenda_clear", self.agenda.clear_events)
        c.register("agenda_next", self.agenda.next_event)

        # Aleatoire
        c.register("random_coin", self.random_picker.flip_coin)
        c.register("random_dice", self.random_picker.roll_dice)
        c.register("random_pick", self.random_picker.pick)
        c.register("random_number", self.random_picker.random_num)

        # Abreviations
        c.register("abbrev_define", self.abbreviations.define)
        c.register("abbrev_list", self.abbreviations.list_category)

        # Automatisation
        c.register("automation_create", self.automation.create)
        c.register("automation_run", self._run_macro)

        # Navigation avancee (browser memory + Playwright)
        c.register("browser_bookmark", self._browser_bookmark)
        c.register("browser_bookmarks_list", self._browser_bookmarks_list)
        c.register("browser_history", self._browser_history)
        c.register("browser_search_history", self._browser_search_history)
        c.register("browser_goto_remembered", self._browser_goto)
        c.register("browser_landmarks", self._browser_landmarks)
        c.register("browser_scroll_to", self._browser_scroll_to)
        c.register("browser_summarize", self._browser_summarize)
        c.register("browser_add_note", self._browser_add_note)
        c.register("browser_save_session", self._browser_save_session)
        c.register("browser_restore_session", self._browser_restore_session)
        c.register("browser_most_visited", self._browser_most_visited)
        c.register("browser_read", self._browser_read)
        c.register("browser_click", self._browser_click)

        # Contrôle JARVIS
        c.register("jarvis_help", self._help)
        c.register("jarvis_status", self._status)
        c.register("jarvis_quit", self._quit)
        c.register("jarvis_thanks", self._thanks)
        c.register("jarvis_cancel", self._cancel)
        c.register("jarvis_repeat", self._repeat)
        c.register("jarvis_settings", self.navigation.open_settings)
        c.register("unknown", self._unknown)

    async def process_transcription(self, text: str, is_partial: bool = False):
        """
        Point d'entrée principal: traite le texte transcrit par Whisper-Flow.
        Appelé à chaque segment final de transcription.
        """
        if is_partial or not text or not text.strip():
            return

        text = text.strip()
        logger.info(f"Transcription reçue: '{text}'")

        # Mode dictée actif - traite comme texte à taper
        if self.dictation.active:
            if self.dictation.should_stop(text):
                result = await self.dictation.stop(
                    VoiceCommand(text, "dictation_stop")
                )
                await self.tts.speak_status(result.message)
            else:
                await self.dictation.process_text(text)
            return

        # Mode macro enregistrement
        if self.automation.recording:
            if "fin de macro" in text.lower() or "stop macro" in text.lower():
                result = await self.automation.stop_recording()
                await self.tts.speak(result.message)
                return
            self.automation.record_step(text)
            return

        # Détection du wake word "Jarvis"
        detected, command_text = detect_wake_word(text)

        if not detected:
            return

        if not command_text:
            await self.tts.speak_status("wake")
            return

        # Parse et exécute la commande
        result = await self.commander.process_text(command_text)

        # Gère les actions en attente (shutdown, restart)
        if result.data and "pending_action" in result.data:
            self._pending_action = result.data

        # Réponse vocale
        if result.message:
            if result.message in ("dictation_on", "dictation_off"):
                await self.tts.speak_status(result.message)
            elif result.success:
                await self.tts.speak(result.message)
            else:
                await self.tts.speak(f"Désolé. {result.message}")

    # === Handlers internes ===

    async def _help(self, command: VoiceCommand) -> CommandResult:
        return CommandResult(True,
            "Je peux ouvrir des applications, gérer les fenêtres, "
            "contrôler le volume et la luminosité, chercher des fichiers, "
            "naviguer sur le web, dicter du texte, et bien plus. "
            "Dites 'Jarvis' suivi de votre commande."
        )

    async def _status(self, command: VoiceCommand) -> CommandResult:
        intents = len(self.commander.list_intents())
        macros = len(self.automation.macros)
        dictation = "actif" if self.dictation.active else "inactif"
        return CommandResult(True,
            f"JARVIS opérationnel. {intents} commandes disponibles, "
            f"{macros} macros, dictée {dictation}."
        )

    async def _quit(self, command: VoiceCommand) -> CommandResult:
        self._running = False
        return CommandResult(True, "Au revoir. À bientôt.")

    async def _thanks(self, command: VoiceCommand) -> CommandResult:
        return CommandResult(True, "Je vous en prie.")

    async def _cancel(self, command: VoiceCommand) -> CommandResult:
        if self._pending_action:
            await self.system_control.cancel_pending()
            self._pending_action = None
            return CommandResult(True, "Action annulée")
        return CommandResult(True, "Rien à annuler")

    async def _repeat(self, command: VoiceCommand) -> CommandResult:
        last = self.commander.last_command
        if last and last.intent != "jarvis_repeat":
            result = await self.commander.execute(last)
            return result
        return CommandResult(False, "Aucune commande à répéter")

    async def _unknown(self, command: VoiceCommand) -> CommandResult:
        """Commande non reconnue → cluster race M1/OL1 + cowork dispatch."""
        text = command.target or command.raw_text

        # System keywords → try cowork scripts in parallel with LLM
        sys_keywords = {"gpu", "cpu", "ram", "thermal", "disque", "réseau",
                        "processus", "service", "firewall", "driver", "audit"}
        is_sys_query = any(kw in text.lower() for kw in sys_keywords)

        try:
            if is_sys_query:
                # Parallel: cowork + cluster
                cowork_task = asyncio.create_task(dispatch_cowork(text))
                cluster_task = asyncio.create_task(cluster_race(text))
                done, _ = await asyncio.wait(
                    [cowork_task, cluster_task],
                    timeout=15, return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    result = task.result()
                    if isinstance(result, tuple):
                        reply, agent = result
                    elif isinstance(result, str):
                        reply, agent = result, "COWORK"
                    else:
                        continue
                    if reply:
                        logger.info(f"[{agent}] → {str(reply)[:80]}")
                        return CommandResult(True, str(reply))
            else:
                reply, agent = await cluster_race(text)
                if reply:
                    logger.info(f"Cluster [{agent}] → {reply[:80]}")
                    return CommandResult(True, reply)
        except Exception as e:
            logger.warning(f"Pipeline failed: {e}")

        return CommandResult(False,
            f"Je n'ai pas compris '{command.target}'. "
            f"Dites 'aide' pour la liste des commandes."
        )

    async def _run_macro(self, command: VoiceCommand) -> CommandResult:
        result = await self.automation.run(command)
        if result.success and result.data and "macro_steps" in result.data:
            for step in result.data["macro_steps"]:
                await self.commander.process_text(step)
                await asyncio.sleep(0.5)
            return CommandResult(True, "Macro terminée")
        return result

    async def _nav_downloads(self, command: VoiceCommand) -> CommandResult:
        cmd = VoiceCommand("téléchargements", "navigate_folder", target="téléchargements")
        return await self.navigation.navigate(cmd)

    async def _nav_documents(self, command: VoiceCommand) -> CommandResult:
        cmd = VoiceCommand("documents", "navigate_folder", target="documents")
        return await self.navigation.navigate(cmd)

    async def _nav_desktop(self, command: VoiceCommand) -> CommandResult:
        cmd = VoiceCommand("bureau", "navigate_folder", target="bureau")
        return await self.navigation.navigate(cmd)

    # === Browser avance (delegation vers src.commands_browser) ===

    async def _browser_exec(self, name: str, params: dict = None) -> CommandResult:
        """Execute une commande browser via le module turbo."""
        try:
            from src.commands_browser import execute_browser_command
            result = await execute_browser_command(name, params)
            if result.get("status") == "error":
                return CommandResult(False, result.get("error", "Erreur navigateur"))
            # Format voice-friendly response
            r = result.get("result", result)
            if isinstance(r, str):
                return CommandResult(True, r)
            if isinstance(r, dict):
                msg = r.get("message", r.get("title", r.get("summary", str(r)[:200])))
                return CommandResult(True, str(msg)[:300])
            if isinstance(r, list):
                lines = [str(item)[:80] for item in r[:5]]
                return CommandResult(True, ". ".join(lines) if lines else "Aucun resultat")
            return CommandResult(True, str(r)[:300])
        except ImportError:
            return CommandResult(False, "Module navigateur non disponible")
        except Exception as e:
            logger.warning(f"Browser command {name} failed: {e}")
            return CommandResult(False, f"Erreur: {e}")

    async def _browser_bookmark(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_bookmark")

    async def _browser_bookmarks_list(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_bookmarks_list")

    async def _browser_history(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_history")

    async def _browser_search_history(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_search_history", {"query": cmd.target})

    async def _browser_goto(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_goto_remembered", {"name": cmd.target})

    async def _browser_landmarks(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_landmarks")

    async def _browser_scroll_to(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_scroll_to", {"text": cmd.target})

    async def _browser_summarize(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_summarize")

    async def _browser_add_note(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_add_note", {"note": cmd.target})

    async def _browser_save_session(self, cmd: VoiceCommand) -> CommandResult:
        name = cmd.target if cmd.target else f"session_{int(__import__('time').time())}"
        return await self._browser_exec("browser_save_session", {"name": name})

    async def _browser_restore_session(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_restore_session", {"name": cmd.target})

    async def _browser_most_visited(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_most_visited")

    async def _browser_read(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_read")

    async def _browser_click(self, cmd: VoiceCommand) -> CommandResult:
        return await self._browser_exec("browser_click", {"text": cmd.target})

    @property
    def is_running(self):
        return self._running

    async def start(self):
        """Démarre JARVIS"""
        self._running = True
        logger.info("JARVIS démarré")
        await self.tts.speak_status("ready")

    async def stop(self):
        """Arrête JARVIS"""
        self._running = False
        await self.tts.speak_status("goodbye")
        logger.info("JARVIS arrêté")
