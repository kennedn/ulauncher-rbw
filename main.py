# noqa: INP001
"""rbw ulauncher extension."""

import logging
import subprocess
import time

from ulauncher.api import Extension, Result
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.internals import actions


class RbwExtension(Extension):
    """rbw extension."""

    def on_input(self, input_text: str, trigger_id: str) -> list:  # noqa: ARG002
        """Filter entries by input_text."""
        matching = [s for s in entries if input_text in s[1] + s[2]]

        for entry in matching:
            data = {"id": entry[0]}
            yield Result(
                name=entry[1],
                description=entry[2],
                on_enter=ExtensionCustomAction(data),
            )

    def on_item_enter(self, data: dict) -> None:
        """Copy password for entry to clipboard."""
        # logging.info("rbw extension: entry selected: id=%s", data["id"])
        pw = subprocess.check_output(["rbw", "get", data["id"]]).decode("utf-8")  # noqa: S607

        return actions.copy(pw)


if __name__ == "__main__":
    logging.info("rbw extension: started")
    # TODO: Remove while loop when https://github.com/Ulauncher/Ulauncher/issues/1063
    # is merged
    entries = []
    while entries == []:
        try:
            entries_str = subprocess.check_output(
                ["rbw", "list", "--fields", "id,name,user"]  # noqa: S607
            ).decode("utf-8")
            entries_raw = entries_str.splitlines()
            entries = [entry.split("\t") for entry in entries_raw]
            logging.info("rbw extension: Loaded entries %s", len(entries))
        except subprocess.CalledProcessError as err:
            logging.critical("rbw extension: rbw list failed: Pin entry cancelled ?")
            logging.critical(err.output)
        except subprocess.Exception as err:
            logging.critical("rbw extension: rbw list failed: Unkown execption:")
            logging.critical(err.output)
        time.sleep(1)

    RbwExtension().run()
