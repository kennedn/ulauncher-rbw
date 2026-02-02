from __future__ import annotations

import subprocess
from typing import List, Tuple

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction


Entry = Tuple[str, str, str]  # (id, name, user)
MAX_RESULTS = 10


def _run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd).decode("utf-8", errors="replace")


def rbw_list_entries() -> List[Entry]:
    out = _run(["rbw", "list", "--fields", "id,name,user"])  # noqa: S607
    entries: List[Entry] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            entries.append((parts[0], parts[1], parts[2]))
    return entries


def rbw_get_password(entry_id: str) -> str:
    return _run(["rbw", "get", entry_id]).strip()  # noqa: S607


class RbwExtension(Extension):
    def __init__(self):
        super(RbwExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):  # noqa: ARG002
        query = (event.get_argument() or "").strip().lower()
        items = []

        # If no query, show nothing (same behavior as the reference)
        if len(query) < 1:
            return RenderResultListAction(items)

        try:
            entries = rbw_list_entries()
        except Exception as e:  # noqa: BLE001
            items.append(
                ExtensionResultItem(
                    icon="images/bitwarden-icon.png",
                    highlightable=False,
                    name=f"rbw error: {e}",
                    description="rbw may be locked. Unlock it and try again.",
                    on_enter=CopyToClipboardAction(str(e)),
                )
            )
            return RenderResultListAction(items)

        matches = [
            (entry_id, name, user)
            for (entry_id, name, user) in entries
            if query in (name + " " + user).lower()
        ][:MAX_RESULTS]

        if not matches:
            items.append(
                ExtensionResultItem(
                    icon="images/bitwarden-icon.png",
                    highlightable=False,
                    name="No matches",
                    description="Try a different search.",
                    on_enter=CopyToClipboardAction(""),
                )
            )
            return RenderResultListAction(items)

        # Reference-style: each row has CopyToClipboardAction directly.
        # We fetch the password for each displayed item (max 10).
        for entry_id, name, user in matches:
            try:
                pw = rbw_get_password(entry_id)
                desc = "Press 'enter' to copy password to clipboard."
                on_enter = CopyToClipboardAction(pw)
            except Exception as e:  # noqa: BLE001
                desc = "Failed to fetch password (is rbw locked?)."
                on_enter = CopyToClipboardAction("")
                pw = ""  # not used; keep simple

            items.append(
                ExtensionResultItem(
                    icon="images/bitwarden-icon.png",
                    name=name,
                    description=user if user else desc,
                    on_enter=on_enter,
                )
            )

        return RenderResultListAction(items)


if __name__ == "__main__":
    RbwExtension().run()

