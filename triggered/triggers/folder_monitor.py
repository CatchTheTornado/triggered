import asyncio
import os
from pathlib import Path
from typing import Dict, Any

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..config_schema import ConfigSchema, ConfigField


@register_trigger("folder-monitor")
class FolderMonitorTrigger(Trigger):
    """Trigger that fires whenever a file changes in the specified folder.

    Config keys:
    - path: str, directory to watch
    - interval: int, polling interval (seconds, default 5)
    """

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this trigger type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="name",
                type="string",
                description="Trigger name",
                required=True
            ),
            ConfigField(
                name="path",
                type="string",
                description="Directory path to monitor for changes",
                required=True
            ),
            ConfigField(
                name="patterns",
                type="array",
                description="File patterns to monitor (e.g. ['*.txt', '*.log'])",
                default=["*"],
                required=False
            ),
            ConfigField(
                name="events",
                type="array",
                description="Events to monitor (created, modified, deleted)",
                default=["created", "modified", "deleted"],
                required=False
            ),
            ConfigField(
                name="recursive",
                type="boolean",
                description="Whether to monitor subdirectories",
                default=False,
                required=False
            ),
            ConfigField(
                name="interval",
                type="integer",
                description="Polling interval in seconds",
                default=5,
                required=False
            )
        ])

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.path = Path(config["path"]).expanduser().resolve()
        self.interval = int(config.get("interval", 5))
        self.patterns = config.get("patterns", ["*"])
        self.events = config.get("events", ["created", "modified", "deleted"])
        self.recursive = config.get("recursive", False)
        self._snapshot = self._hash_dir()

    def _hash_dir(self):
        """Return a mapping {filepath: mtime}."""
        mapping = {}
        for root, _, files in os.walk(self.path):
            for f in files:
                fp = Path(root) / f
                if not self.recursive and fp.parent != self.path:
                    continue
                if any(fp.match(pattern) for pattern in self.patterns):
                    mapping[str(fp)] = fp.stat().st_mtime
        return mapping

    async def watch(self, queue_put):
        while True:
            await asyncio.sleep(self.interval)
            new_snapshot = self._hash_dir()
            if new_snapshot != self._snapshot:
                # Find changed files
                changed_files = []
                for filepath, mtime in new_snapshot.items():
                    old_mtime = self._snapshot.get(filepath)
                    if old_mtime is None:
                        changed_files.append((filepath, "created"))
                    elif old_mtime != mtime:
                        changed_files.append((filepath, "modified"))
                
                # Find deleted files
                for filepath in self._snapshot:
                    if filepath not in new_snapshot:
                        changed_files.append((filepath, "deleted"))
                
                # Update snapshot
                self._snapshot = new_snapshot
                
                # Create context for each changed file
                for filepath, event in changed_files:
                    if event in self.events:
                        filename = Path(filepath).name
                        ctx = TriggerContext(
                            trigger_name=self.name,
                            data={
                                "filename": filename,
                                "filepath": filepath,
                                "event": event
                            },
                        )
                        await queue_put(ctx)

            ctx = TriggerContext(trigger_name=self.name)
            await queue_put(ctx) 