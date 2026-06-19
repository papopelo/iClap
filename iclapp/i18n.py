"""Internacionalización de iClapp (textos visibles al usuario).

Resuelve el idioma en este orden: lo que diga la config (`language`), y si está
en "auto" (o vacío), el idioma del sistema macOS; si nada coincide, inglés.

Uso:
    from .i18n import t, LANGUAGES, set_language
    t("app.pause")                      -> "Pausar" / "Pause" / ...
    t("prefs.current", threshold=0.45, max_clap_ms=160)

Agregar un idioma = añadir su código a LANGUAGES y una entrada por clave abajo.
La cadena cae a inglés, luego español, y por último a la propia clave si falta.
"""

import os
import re
import subprocess

# Idiomas soportados: código -> nombre nativo (para mostrar en el selector).
LANGUAGES = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
}
FALLBACK = "en"

_current = None  # código resuelto y cacheado; None = aún sin resolver


# --- Detección del idioma del sistema --------------------------------------
def _primary_system_code():
    """Código de 2 letras del idioma PRINCIPAL del Mac (1er ítem de AppleLanguages).

    Mira solo el idioma principal: si ese no está soportado, NO baja al segundo
    de la lista (la app caerá a inglés). Devuelve p.ej. 'it' para un Mac en
    italiano ('it-IT'), o None si no se puede leer.
    """
    try:
        out = subprocess.run(
            ["defaults", "read", "-g", "AppleLanguages"],
            capture_output=True, text=True, timeout=2,
        ).stdout
    except Exception:  # noqa: BLE001
        return None
    # AppleLanguages se ve así:  (\n    "it-IT",\n    "en-US"\n)
    entries = re.findall(r'"([^"]+)"', out)
    primary = entries[0] if entries else out.strip()
    return primary[:2].lower() if primary else None


def _system_lang():
    """Idioma principal del Mac si iClapp lo soporta; si no, las env vars; o inglés."""
    code = _primary_system_code()
    if code not in LANGUAGES:
        env = (os.environ.get("LANG") or os.environ.get("LC_ALL") or "")[:2].lower()
        code = env if env in LANGUAGES else None
    return code if code in LANGUAGES else FALLBACK


def resolve(lang=None):
    """Normaliza `lang` (o lee la config si es None) a un código soportado."""
    if lang is None:
        try:
            from . import config
            lang = config.load().get("language", "auto")
        except Exception:  # noqa: BLE001
            lang = "auto"
    if lang in LANGUAGES:
        return lang
    return _system_lang()


def get_language():
    """Código de idioma activo (lo resuelve y cachea la primera vez)."""
    global _current
    if _current is None:
        _current = resolve()
    return _current


def set_language(lang):
    """Fija el idioma activo explícitamente (p.ej. desde la flag --lang)."""
    global _current
    _current = lang if lang in LANGUAGES else resolve(lang)


def refresh():
    """Olvida el idioma cacheado para volver a resolverlo desde la config."""
    global _current
    _current = None


def t(key, **kw):
    """Traduce `key` al idioma activo y formatea con `kw` (str.format)."""
    lang = get_language()
    table = TRANSLATIONS.get(key, {})
    s = table.get(lang) or table.get(FALLBACK) or table.get("es") or key
    if kw:
        try:
            s = s.format(**kw)
        except Exception:  # noqa: BLE001
            pass
    return s


# --- Tabla de traducciones --------------------------------------------------
# clave -> {código de idioma: cadena}. Los emojis se mantienen iguales en todos.
TRANSLATIONS = {
    # Barra de menú (app.py)
    "app.starting": {
        "es": "Iniciando…", "en": "Starting…", "pt": "Iniciando…",
        "fr": "Démarrage…", "de": "Wird gestartet…", "it": "Avvio…",
    },
    "app.pause": {
        "es": "Pausar", "en": "Pause", "pt": "Pausar",
        "fr": "Pause", "de": "Pausieren", "it": "Pausa",
    },
    "app.resume": {
        "es": "Reanudar", "en": "Resume", "pt": "Retomar",
        "fr": "Reprendre", "de": "Fortsetzen", "it": "Riprendi",
    },
    "app.preferences": {
        "es": "Preferencias…", "en": "Preferences…", "pt": "Preferências…",
        "fr": "Préférences…", "de": "Einstellungen…", "it": "Preferenze…",
    },
    "app.quit": {
        "es": "Salir de iClapp", "en": "Quit iClapp", "pt": "Sair do iClapp",
        "fr": "Quitter iClapp", "de": "iClapp beenden", "it": "Esci da iClapp",
    },
    "app.listening": {
        "es": "🎧 Escuchando · {mic}", "en": "🎧 Listening · {mic}",
        "pt": "🎧 Ouvindo · {mic}", "fr": "🎧 À l'écoute · {mic}",
        "de": "🎧 Höre zu · {mic}", "it": "🎧 In ascolto · {mic}",
    },
    "app.default_mic": {
        "es": "micrófono por defecto", "en": "default microphone",
        "pt": "microfone padrão", "fr": "microphone par défaut",
        "de": "Standardmikrofon", "it": "microfono predefinito",
    },
    "app.mic_error": {
        "es": "⚠️ Error de micrófono (revisa permisos)",
        "en": "⚠️ Microphone error (check permissions)",
        "pt": "⚠️ Erro de microfone (verifique as permissões)",
        "fr": "⚠️ Erreur de microphone (vérifiez les autorisations)",
        "de": "⚠️ Mikrofonfehler (Berechtigungen prüfen)",
        "it": "⚠️ Errore del microfono (controlla i permessi)",
    },
    "app.paused": {
        "es": "⏸️ En pausa", "en": "⏸️ Paused", "pt": "⏸️ Em pausa",
        "fr": "⏸️ En pause", "de": "⏸️ Pausiert", "it": "⏸️ In pausa",
    },
    "app.prefs_open": {
        "es": "⚙️ Preferencias abiertas…", "en": "⚙️ Preferences open…",
        "pt": "⚙️ Preferências abertas…", "fr": "⚙️ Préférences ouvertes…",
        "de": "⚙️ Einstellungen geöffnet…", "it": "⚙️ Preferenze aperte…",
    },

    # Ventana de Preferencias (prefs.py)
    "prefs.title": {
        "es": "iClapp — Preferencias", "en": "iClapp — Preferences",
        "pt": "iClapp — Preferências", "fr": "iClapp — Préférences",
        "de": "iClapp — Einstellungen", "it": "iClapp — Preferenze",
    },
    "prefs.mic_label": {
        "es": "🎙️  Micrófono de entrada", "en": "🎙️  Input microphone",
        "pt": "🎙️  Microfone de entrada", "fr": "🎙️  Microphone d'entrée",
        "de": "🎙️  Eingabemikrofon", "it": "🎙️  Microfono di ingresso",
    },
    "prefs.default_device": {
        "es": "Dispositivo por defecto", "en": "Default device",
        "pt": "Dispositivo padrão", "fr": "Périphérique par défaut",
        "de": "Standardgerät", "it": "Dispositivo predefinito",
    },
    "prefs.url_label": {
        "es": "🔗  URL a reproducir (Spotify / Apple Music / YouTube Music)",
        "en": "🔗  URL to play (Spotify / Apple Music / YouTube Music)",
        "pt": "🔗  URL para reproduzir (Spotify / Apple Music / YouTube Music)",
        "fr": "🔗  URL à lire (Spotify / Apple Music / YouTube Music)",
        "de": "🔗  Abzuspielende URL (Spotify / Apple Music / YouTube Music)",
        "it": "🔗  URL da riprodurre (Spotify / Apple Music / YouTube Music)",
    },
    "prefs.url_hint": {
        "es": "Soporta canción, álbum o playlist (pega el enlace).",
        "en": "Supports a song, album or playlist (paste the link).",
        "pt": "Suporta música, álbum ou playlist (cole o link).",
        "fr": "Prend en charge une chanson, un album ou une playlist (collez le lien).",
        "de": "Unterstützt Song, Album oder Playlist (Link einfügen).",
        "it": "Supporta canzone, album o playlist (incolla il link).",
    },
    "prefs.shuffle": {
        "es": "Reproducir en shuffle (Spotify / Apple Music)",
        "en": "Play on shuffle (Spotify / Apple Music)",
        "pt": "Reproduzir aleatório (Spotify / Apple Music)",
        "fr": "Lecture aléatoire (Spotify / Apple Music)",
        "de": "Zufallswiedergabe (Spotify / Apple Music)",
        "it": "Riproduci in modalità casuale (Spotify / Apple Music)",
    },
    "prefs.language_label": {
        "es": "🌐  Idioma", "en": "🌐  Language", "pt": "🌐  Idioma",
        "fr": "🌐  Langue", "de": "🌐  Sprache", "it": "🌐  Lingua",
    },
    "prefs.language_auto": {
        "es": "Automático (según el sistema)", "en": "Automatic (system)",
        "pt": "Automático (sistema)", "fr": "Automatique (système)",
        "de": "Automatisch (System)", "it": "Automatico (sistema)",
    },
    "prefs.language_note": {
        "es": "El cambio se aplica al reabrir la app.",
        "en": "The change takes effect when you reopen the app.",
        "pt": "A mudança é aplicada ao reabrir o app.",
        "fr": "Le changement s'applique à la réouverture de l'app.",
        "de": "Die Änderung wird beim erneuten Öffnen der App wirksam.",
        "it": "La modifica si applica alla riapertura dell'app.",
    },
    "prefs.calibrate": {
        "es": "🎚️  Calibrar aplausos", "en": "🎚️  Calibrate claps",
        "pt": "🎚️  Calibrar palmas", "fr": "🎚️  Calibrer les applaudissements",
        "de": "🎚️  Klatschen kalibrieren", "it": "🎚️  Calibra gli applausi",
    },
    "prefs.current": {
        "es": "Actual: umbral {threshold}, {max_clap_ms} ms",
        "en": "Current: threshold {threshold}, {max_clap_ms} ms",
        "pt": "Atual: limiar {threshold}, {max_clap_ms} ms",
        "fr": "Actuel : seuil {threshold}, {max_clap_ms} ms",
        "de": "Aktuell: Schwelle {threshold}, {max_clap_ms} ms",
        "it": "Attuale: soglia {threshold}, {max_clap_ms} ms",
    },
    "prefs.cancel": {
        "es": "Cancelar", "en": "Cancel", "pt": "Cancelar",
        "fr": "Annuler", "de": "Abbrechen", "it": "Annulla",
    },
    "prefs.save": {
        "es": "Guardar", "en": "Save", "pt": "Salvar",
        "fr": "Enregistrer", "de": "Speichern", "it": "Salva",
    },
    "prefs.clap_prompt": {
        "es": "Aplaude 5 veces, una a una…", "en": "Clap 5 times, one by one…",
        "pt": "Bata palmas 5 vezes, uma a uma…",
        "fr": "Applaudissez 5 fois, une à une…",
        "de": "Klatsche 5 Mal, einzeln…", "it": "Applaudi 5 volte, una alla volta…",
    },
    "prefs.captured": {
        "es": "👏 {i}/{n} capturados…", "en": "👏 {i}/{n} captured…",
        "pt": "👏 {i}/{n} capturados…", "fr": "👏 {i}/{n} capturés…",
        "de": "👏 {i}/{n} erfasst…", "it": "👏 {i}/{n} acquisiti…",
    },
    "prefs.error": {
        "es": "Error: {msg}", "en": "Error: {msg}", "pt": "Erro: {msg}",
        "fr": "Erreur : {msg}", "de": "Fehler: {msg}", "it": "Errore: {msg}",
    },
    "prefs.few_claps": {
        "es": "Pocos aplausos. Revisa el micrófono y reintenta.",
        "en": "Too few claps. Check the microphone and try again.",
        "pt": "Poucas palmas. Verifique o microfone e tente novamente.",
        "fr": "Trop peu d'applaudissements. Vérifiez le microphone et réessayez.",
        "de": "Zu wenig Klatschen. Mikrofon prüfen und erneut versuchen.",
        "it": "Troppo pochi applausi. Controlla il microfono e riprova.",
    },
    "prefs.calibrated": {
        "es": "✅ Calibrado: umbral {threshold}, {max_clap_ms} ms",
        "en": "✅ Calibrated: threshold {threshold}, {max_clap_ms} ms",
        "pt": "✅ Calibrado: limiar {threshold}, {max_clap_ms} ms",
        "fr": "✅ Calibré : seuil {threshold}, {max_clap_ms} ms",
        "de": "✅ Kalibriert: Schwelle {threshold}, {max_clap_ms} ms",
        "it": "✅ Calibrato: soglia {threshold}, {max_clap_ms} ms",
    },

    # Reproducción (players.py)
    "players.unknown_url": {
        "es": "URL no reconocida (usa Spotify, Apple Music o YouTube Music).",
        "en": "Unrecognized URL (use Spotify, Apple Music or YouTube Music).",
        "pt": "URL não reconhecido (use Spotify, Apple Music ou YouTube Music).",
        "fr": "URL non reconnue (utilisez Spotify, Apple Music ou YouTube Music).",
        "de": "URL nicht erkannt (verwende Spotify, Apple Music oder YouTube Music).",
        "it": "URL non riconosciuto (usa Spotify, Apple Music o YouTube Music).",
    },
    "players.youtube": {
        "es": "▶️ YouTube Music (en el navegador)",
        "en": "▶️ YouTube Music (in the browser)",
        "pt": "▶️ YouTube Music (no navegador)",
        "fr": "▶️ YouTube Music (dans le navigateur)",
        "de": "▶️ YouTube Music (im Browser)",
        "it": "▶️ YouTube Music (nel browser)",
    },
    "players.play_error": {
        "es": "Error al reproducir: {detail}", "en": "Playback error: {detail}",
        "pt": "Erro ao reproduzir: {detail}", "fr": "Erreur de lecture : {detail}",
        "de": "Wiedergabefehler: {detail}", "it": "Errore di riproduzione: {detail}",
    },
    "players.unsupported": {
        "es": "Servicio no soportado.", "en": "Unsupported service.",
        "pt": "Serviço não suportado.", "fr": "Service non pris en charge.",
        "de": "Nicht unterstützter Dienst.", "it": "Servizio non supportato.",
    },

    # Calibración por terminal (calibrate.py)
    "cal.intro": {
        "es": "🎚️  Calibración: aplaude {n} veces, una a una, con ~1 s entre cada una.",
        "en": "🎚️  Calibration: clap {n} times, one by one, with ~1 s between each.",
        "pt": "🎚️  Calibração: bata palmas {n} vezes, uma a uma, com ~1 s entre cada.",
        "fr": "🎚️  Calibration : applaudissez {n} fois, une à une, avec ~1 s entre chaque.",
        "de": "🎚️  Kalibrierung: klatsche {n} Mal, einzeln, mit ~1 s dazwischen.",
        "it": "🎚️  Calibrazione: applaudi {n} volte, una alla volta, con ~1 s tra ognuna.",
    },
    "cal.cancel_hint": {
        "es": "   (Ctrl+C para cancelar)", "en": "   (Ctrl+C to cancel)",
        "pt": "   (Ctrl+C para cancelar)", "fr": "   (Ctrl+C pour annuler)",
        "de": "   (Ctrl+C zum Abbrechen)", "it": "   (Ctrl+C per annullare)",
    },
    "cal.clap": {
        "es": "   👏 {i}/{total}  pico:{peak}  dur:{dur}ms",
        "en": "   👏 {i}/{total}  peak:{peak}  dur:{dur}ms",
        "pt": "   👏 {i}/{total}  pico:{peak}  dur:{dur}ms",
        "fr": "   👏 {i}/{total}  crête:{peak}  dur:{dur}ms",
        "de": "   👏 {i}/{total}  Spitze:{peak}  Dauer:{dur}ms",
        "it": "   👏 {i}/{total}  picco:{peak}  dur:{dur}ms",
    },
    "cal.cancelled": {
        "es": "✋ Cancelada.", "en": "✋ Cancelled.", "pt": "✋ Cancelada.",
        "fr": "✋ Annulé.", "de": "✋ Abgebrochen.", "it": "✋ Annullato.",
    },
    "cal.too_few": {
        "es": "⚠️  Solo detecté {n} aplauso(s). Revisa el permiso de micrófono y "
              "aplaude más fuerte/cerca; reintenta.",
        "en": "⚠️  Only detected {n} clap(s). Check the microphone permission and "
              "clap louder/closer; try again.",
        "pt": "⚠️  Detectei apenas {n} palma(s). Verifique a permissão do microfone "
              "e bata mais forte/perto; tente novamente.",
        "fr": "⚠️  Seulement {n} applaudissement(s) détecté(s). Vérifiez "
              "l'autorisation du microphone et applaudissez plus fort/près ; réessayez.",
        "de": "⚠️  Nur {n} Klatschen erkannt. Mikrofonberechtigung prüfen und "
              "lauter/näher klatschen; erneut versuchen.",
        "it": "⚠️  Rilevati solo {n} applauso(i). Controlla il permesso del microfono "
              "e applaudi più forte/vicino; riprova.",
    },
    "cal.saved": {
        "es": "✅ Calibrado: threshold={threshold}, max_clap_ms={max_clap_ms} (guardado).",
        "en": "✅ Calibrated: threshold={threshold}, max_clap_ms={max_clap_ms} (saved).",
        "pt": "✅ Calibrado: threshold={threshold}, max_clap_ms={max_clap_ms} (salvo).",
        "fr": "✅ Calibré : threshold={threshold}, max_clap_ms={max_clap_ms} (enregistré).",
        "de": "✅ Kalibriert: threshold={threshold}, max_clap_ms={max_clap_ms} (gespeichert).",
        "it": "✅ Calibrato: threshold={threshold}, max_clap_ms={max_clap_ms} (salvato).",
    },

    # CLI headless (__main__.py)
    "cli.desc": {
        "es": "iClapp — música al aplaudir dos veces.",
        "en": "iClapp — music when you clap twice.",
        "pt": "iClapp — música ao bater palmas duas vezes.",
        "fr": "iClapp — de la musique quand vous applaudissez deux fois.",
        "de": "iClapp — Musik, wenn du zweimal klatschst.",
        "it": "iClapp — musica applaudendo due volte.",
    },
    "cli.help_calibrate": {
        "es": "Mide tus aplausos y ajusta la sensibilidad.",
        "en": "Measure your claps and adjust the sensitivity.",
        "pt": "Mede suas palmas e ajusta a sensibilidade.",
        "fr": "Mesure vos applaudissements et ajuste la sensibilité.",
        "de": "Misst dein Klatschen und passt die Empfindlichkeit an.",
        "it": "Misura i tuoi applausi e regola la sensibilità.",
    },
    "cli.help_list": {
        "es": "Lista los micrófonos de entrada disponibles.",
        "en": "List the available input microphones.",
        "pt": "Lista os microfones de entrada disponíveis.",
        "fr": "Liste les microphones d'entrée disponibles.",
        "de": "Listet die verfügbaren Eingabemikrofone auf.",
        "it": "Elenca i microfoni di ingresso disponibili.",
    },
    "cli.help_url": {
        "es": "Sobrescribe la URL a reproducir.", "en": "Override the URL to play.",
        "pt": "Substitui o URL a reproduzir.", "fr": "Remplace l'URL à lire.",
        "de": "Überschreibt die abzuspielende URL.",
        "it": "Sovrascrive l'URL da riprodurre.",
    },
    "cli.help_noshuffle": {
        "es": "Sin shuffle.", "en": "No shuffle.", "pt": "Sem shuffle.",
        "fr": "Sans lecture aléatoire.", "de": "Ohne Zufallswiedergabe.",
        "it": "Senza riproduzione casuale.",
    },
    "cli.help_lang": {
        "es": "Fuerza el idioma (es, en, pt, fr, de, it).",
        "en": "Force the language (es, en, pt, fr, de, it).",
        "pt": "Força o idioma (es, en, pt, fr, de, it).",
        "fr": "Force la langue (es, en, pt, fr, de, it).",
        "de": "Erzwingt die Sprache (es, en, pt, fr, de, it).",
        "it": "Forza la lingua (es, en, pt, fr, de, it).",
    },
    "cli.double_clap": {
        "es": "👏👏 doble aplauso", "en": "👏👏 double clap",
        "pt": "👏👏 palma dupla", "fr": "👏👏 double applaudissement",
        "de": "👏👏 Doppelklatschen", "it": "👏👏 doppio applauso",
    },
    "cli.listening": {
        "es": "🎧 Escuchando (micro: {mic}, umbral={threshold}, "
              "dur.máx≈{max_clap_ms}ms). Aplaude DOS veces. Ctrl+C para salir.",
        "en": "🎧 Listening (mic: {mic}, threshold={threshold}, "
              "max dur≈{max_clap_ms}ms). Clap TWICE. Ctrl+C to exit.",
        "pt": "🎧 Ouvindo (mic: {mic}, limiar={threshold}, "
              "dur.máx≈{max_clap_ms}ms). Bata palmas DUAS vezes. Ctrl+C para sair.",
        "fr": "🎧 À l'écoute (micro : {mic}, seuil={threshold}, "
              "dur max≈{max_clap_ms}ms). Applaudissez DEUX fois. Ctrl+C pour quitter.",
        "de": "🎧 Höre zu (Mikro: {mic}, Schwelle={threshold}, "
              "max. Dauer≈{max_clap_ms}ms). Klatsche ZWEIMAL. Ctrl+C zum Beenden.",
        "it": "🎧 In ascolto (mic: {mic}, soglia={threshold}, "
              "dur.max≈{max_clap_ms}ms). Applaudi DUE volte. Ctrl+C per uscire.",
    },
    "cli.default": {
        "es": "por defecto", "en": "default", "pt": "padrão",
        "fr": "par défaut", "de": "Standard", "it": "predefinito",
    },
    "cli.bye": {
        "es": "👋 Hasta luego.", "en": "👋 See you.", "pt": "👋 Até logo.",
        "fr": "👋 À bientôt.", "de": "👋 Bis bald.", "it": "👋 A presto.",
    },
}
