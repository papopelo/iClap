"""Modo headless de iClapp: escucha y reproduce, sin interfaz.

Lo usa el LaunchAgent (segundo plano). Para la app con interfaz, ver iclapp.app.

    python -m iclapp                 # escuchar
    python -m iclapp --calibrate     # recalibrar por terminal
    python -m iclapp --list-devices  # ver micrófonos disponibles
"""

import argparse
import sys
import time

from . import config
from . import i18n
from .calibrate import run_cli as calibrate_cli
from .engine import ClapEngine, list_input_devices
from .i18n import LANGUAGES, t
from .players import play


def main():
    # El idioma de la CLI puede venir por --lang; si no, sale de la config/sistema.
    if "--lang" in sys.argv:
        try:
            i18n.set_language(sys.argv[sys.argv.index("--lang") + 1])
        except (IndexError, ValueError):
            pass

    parser = argparse.ArgumentParser(description=t("cli.desc"))
    parser.add_argument("--calibrate", action="store_true",
                        help=t("cli.help_calibrate"))
    parser.add_argument("--list-devices", action="store_true",
                        help=t("cli.help_list"))
    parser.add_argument("--url", help=t("cli.help_url"))
    parser.add_argument("--no-shuffle", action="store_true", help=t("cli.help_noshuffle"))
    parser.add_argument("--lang", choices=list(LANGUAGES), help=t("cli.help_lang"))
    args = parser.parse_args()

    if args.list_devices:
        for name, idx in list_input_devices():
            print(f"  [{idx}] {name}")
        return

    if args.calibrate:
        calibrate_cli()
        return

    cfg = config.load()
    url = args.url or cfg["url"]
    shuffle = cfg["shuffle"] and not args.no_shuffle

    def on_clap():
        print(t("cli.double_clap"))
        ok, msg = play(url, shuffle)
        print(("✅ " if ok else "⚠️  ") + msg, file=sys.stdout if ok else sys.stderr)

    engine = ClapEngine(
        on_double_clap=on_clap,
        threshold=cfg["threshold"],
        max_clap_ms=cfg["max_clap_ms"],
        input_device=cfg.get("input_device"),
    )
    engine.start()
    mic = cfg.get("input_device") or t("cli.default")
    print(t("cli.listening", mic=mic, threshold=cfg["threshold"],
            max_clap_ms=cfg["max_clap_ms"]))
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n" + t("cli.bye"))
    finally:
        engine.stop()


if __name__ == "__main__":
    main()
