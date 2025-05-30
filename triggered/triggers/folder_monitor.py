import asyncio
import os
from pathlib import Path
from typing import Dict, Any

from ..core import Trigger, TriggerContext
from ..registry import register_trigger


@register_trigger("folder")
class FolderMonitorTrigger(Trigger):
    """Trigger that fires whenever a file changes in the specified folder.

    Config keys:
    - path: str, directory to watch
    - interval: int, polling interval (seconds, default 5)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.path = Path(config["path"]).expanduser().resolve()
        self.interval = int(config.get("interval", 5))
        self._snapshot = self._hash_dir()

    def _hash_dir(self):
        """Return a mapping {filepath: mtime}."""
        mapping = {}
        for root, _, files in os.walk(self.path):
            for f in files:
                fp = Path(root) / f
                mapping[str(fp)] = fp.stat().st_mtime
        return mapping

    async def watch(self, queue_put):
        while True:
            await asyncio.sleep(self.interval)
            new_snapshot = self._hash_dir()
            if new_snapshot != self._snapshot:
                diff_files = [
                    k
                    for k in new_snapshot
                    if self._snapshot.get(k) != new_snapshot[k]
                ]
                self._snapshot = new_snapshot
                ctx = TriggerContext(
                    trigger_name=self.name,
                    data={"files_changed": diff_files},
                )
                await queue_put(ctx) 