# noqa: INP001
"""rbw ulauncher extension."""

import logging
import subprocess
import time

import gi

# Ulauncher uses GTK3, so force GTK/GDK 3.0 BEFORE importing gi.repository
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk  # noqa: E402

from ulauncher.api.client.Extension import Extension  # noqa: E402
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction  # noqa: E402
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem as Result  # noqa: E402

logger = logging.getLogger(__name__)

clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

entries = []


class RbwExtension(Extension):
    """rbw extension."""

    def on_input(self, input_text: str, trigger_id: str):  # noqa: ARG002
        """Filter entries by input_text."""
        text = (input_text or "").strip()

        # entries are [id, name, user]
        matching = [
            e for e in entries
            if len(e) >= 3 and (text.lower() in (e[1] + " " + e[2]).lower())
        ]

        for entry_id, name, user, *_rest in matching:
            yield Result(
                name=name,
                description=user,
                on_enter=ExtensionCustomAction({"id": entry_id}),
            )

    def on_item_enter(self, data: dict) -> None:
        """Copy password for entry to clipboard."""
        entry_id = data.get("id")
        if not entry_id:
            return

        pw = subprocess.check_output(["rbw", "get", entry_id]).decode("utf-8").strip()  # noqa: S607
        clipboard.set_text(pw, -1)
        clipboard.store()


def load_entries() -> list:
    """Load rbw entries as a list of [id, name, user]."""
    entries_str = subprocess.check_output(  # noqa: S607
        ["rbw", "list", "--fields", "id,name,user"]
    ).decode("utf-8")

    lines = [ln for ln in entries_str.splitlines() if ln.strip()]
    return [ln.split("\t") for ln in lines]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("rbw extension: started")

    # TODO: Remove while loop when https://github.com/Ulauncher/Ulauncher/issues/1063 is merged
    while not entries:
        try:
            entries = load_entries()
            logger.info("rbw extension: loaded entries=%d", len(entries))
        except subprocess.CalledProcessError as err:
            logger.critical("rbw extension: rbw list failed (pin entry cancelled?)")
            logger.critical(getattr(err, "output", err))
        except Exception as err:  # noqa: BLE001
            logger.critical("rbw extension: rbw list failed: %s", err)
        time.sleep(1)

    RbwExtension().run()

