#!/usr/bin/env python3
"""
Detecta dos aplausos seguidos y reproduce
"Should I Stay or Should I Go" - The Clash en Spotify.

Uso:
    python clap_play.py            # modo normal
    python clap_play.py --debug    # muestra el nivel de audio para calibrar
    python clap_play.py --threshold 0.4
"""

import argparse
import subprocess
import sys
import time

import numpy as np
import sounddevice as sd

# --- Configuración de la canción ---------------------------------------------
TRACK_URI = "spotify:track:02DZxszCWyn3UivsWTblnq"  # The Clash - Should I Stay or Should I Go

# --- Parámetros de detección -------------------------------------------------
SAMPLERATE = 44100        # Hz
BLOCKSIZE = 1024          # muestras por bloque (~23 ms)
DEFAULT_THRESHOLD = 0.45  # pico de amplitud (0..1) para contar como aplauso
DEFAULT_HF_RATIO = 0.0    # filtro de agudos (0 = desactivado; ver --hf-ratio)
HF_CUTOFF = 2000          # Hz: frontera grave/agudo
MAX_CLAP_MS = 160         # ms: duración máxima de un aplauso (más largo = tos/ruido)
                          # Calibrado 2026-06-18: aplausos ≤139ms (6b), voz/tos ≥186ms (8b);
                          # corte en 7 bloques (~162ms) separa limpio ambos.
SUSTAIN_FACTOR = 0.5      # fracción del umbral para medir la "cola" del sonido
BLOCK_MS = 1000.0 * BLOCKSIZE / SAMPLERATE          # ~23 ms por bloque
DEBOUNCE = 0.15           # s: tiempo mínimo entre dos aplausos (anti-rebote)
DOUBLE_WINDOW = 0.80      # s: ventana máxima entre aplauso 1 y aplauso 2
COOLDOWN = 5.0            # s: pausa tras disparar (evita que la música re-dispare)

# Precálculo para el análisis de frecuencia (ventana Hann + máscara de agudos)
_WINDOW = np.hanning(BLOCKSIZE)
_FREQS = np.fft.rfftfreq(BLOCKSIZE, 1.0 / SAMPLERATE)
_HF_MASK = _FREQS >= HF_CUTOFF


def hf_ratio(block):
    """Fracción de energía espectral por encima de HF_CUTOFF (0..1).

    Aplauso (clic de banda ancha) -> alto. Tos/voz (energía grave) -> bajo.
    """
    x = block[:, 0] if block.ndim > 1 else block
    if len(x) != BLOCKSIZE:
        return 0.0
    mag = np.abs(np.fft.rfft(x * _WINDOW))
    total = mag.sum()
    if total < 1e-9:
        return 0.0
    return float(mag[_HF_MASK].sum() / total)


def play_track():
    """Lanza/usa Spotify y reproduce el track vía AppleScript.

    Si Spotify estaba cerrado, al abrirse a veces queda en pausa; por eso
    cargamos el track, esperamos un poco y forzamos 'play'.
    """
    script = f'''
    if application "Spotify" is not running then
        tell application "Spotify" to activate
        delay 1.5
    end if
    tell application "Spotify"
        play track "{TRACK_URI}"
        delay 0.5
        if player state is not playing then play
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True,
                       capture_output=True, text=True)
        print("🎸 ¡Should I Stay or Should I Go!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Error al reproducir: {e.stderr.strip()}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Reproduce una canción al aplaudir dos veces.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help="Sensibilidad del aplauso (0..1). Más bajo = más sensible.")
    parser.add_argument("--hf-ratio", type=float, default=DEFAULT_HF_RATIO,
                        help="Mínimo de agudos (0..1) para distinguir aplauso de tos/voz.")
    parser.add_argument("--max-clap-ms", type=float, default=MAX_CLAP_MS,
                        help="Duración máxima de un aplauso en ms (más largo = tos/ruido).")
    parser.add_argument("--debug", action="store_true",
                        help="Muestra nivel y agudos para calibrar.")
    args = parser.parse_args()

    sustain = args.threshold * SUSTAIN_FACTOR
    max_clap_blocks = max(1, round(args.max_clap_ms / BLOCK_MS))

    state = {
        "last_clap": 0.0,    # timestamp del último aplauso válido
        "first_clap": 0.0,   # timestamp del primer aplauso de un par
        "muted_until": 0.0,  # cooldown tras disparar
        "run_len": 0,        # bloques consecutivos por encima de 'sustain'
        "run_peak": 0.0,     # pico máximo durante la racha actual
        "run_start": 0.0,    # inicio de la racha actual
    }

    def register_clap(t):
        """Registra un aplauso válido y dispara si es el segundo del par."""
        if (t - state["last_clap"]) < DEBOUNCE:
            return
        if state["first_clap"] and (t - state["first_clap"]) <= DOUBLE_WINDOW:
            if not args.debug:
                print("👏👏 doble aplauso detectado")
            play_track()
            state["first_clap"] = 0.0
            state["muted_until"] = t + COOLDOWN
        else:
            state["first_clap"] = t
        state["last_clap"] = t

    def callback(indata, frames, time_info, status):
        now = time.monotonic()
        peak = float(np.abs(indata).max())
        active = peak >= sustain          # ¿hay sonido relevante en este bloque?

        if now < state["muted_until"]:
            state["run_len"] = 0          # no acumular durante el cooldown
            return

        if active:
            # Estamos dentro de una racha de sonido fuerte: acumular
            if state["run_len"] == 0:
                state["run_start"] = now
                state["run_peak"] = 0.0
            state["run_len"] += 1
            state["run_peak"] = max(state["run_peak"], peak)
        elif state["run_len"] > 0:
            # La racha acaba de terminar -> clasificar
            blocks, rpeak = state["run_len"], state["run_peak"]
            state["run_len"] = 0
            short = blocks <= max_clap_blocks                 # breve = aplauso
            strong = rpeak >= args.threshold                 # suficientemente fuerte
            hf_ok = args.hf_ratio <= 0.0 or hf_ratio(indata) >= args.hf_ratio
            is_clap = short and strong and hf_ok
            if args.debug:
                dur = blocks * BLOCK_MS
                tag = "👏 APLAUSO" if is_clap else ("🗣️ largo/tos" if strong else "ruido")
                print(f" pico:{rpeak:5.3f} dur:{dur:5.0f}ms ({blocks}b) -> {tag}", flush=True)
            if is_clap:
                register_clap(state["run_start"])

        if args.debug and active:
            bars = int(peak * 40)
            print(f"\r nivel:{peak:5.3f} {'█' * bars:<40}", end="", flush=True)

    print("🎧 Escuchando... aplaude DOS veces para reproducir la canción.")
    print(f"   (umbral={args.threshold}, dur.máx≈{args.max_clap_ms:.0f}ms, Ctrl+C para salir)")
    if args.debug:
        print("   [debug: cada sonido muestra su pico y duración; aplauso = breve]\n")

    try:
        with sd.InputStream(channels=1, samplerate=SAMPLERATE,
                            blocksize=BLOCKSIZE, callback=callback):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n👋 Hasta luego.")


if __name__ == "__main__":
    main()
