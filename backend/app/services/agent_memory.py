from __future__ import annotations

from collections import defaultdict


class AgentMemory:
    """
    Simple in-memory task tracker keyed by user_id.
    Intended as a lightweight placeholder until we persist to the DB.
    Each task is stored with its completion status so we can render it later.
    """

    def __init__(self) -> None:
        self._tasks: dict[int, list[dict[str, object]]] = defaultdict(list)

    def add_task(self, user_id: int, description: str) -> None:
        description = description.strip()
        if not description:
            return
        tasks = self._tasks[user_id]
        for task in tasks:
            if task["description"] == description:
                task["completed"] = False
                return

        tasks.append({"description": description, "completed": False})

    def get_tasks(self, user_id: int) -> list[dict[str, object]]:
        return [task.copy() for task in self._tasks.get(user_id, [])]

    def complete_task(self, user_id: int, description: str | None = None) -> None:
        if user_id not in self._tasks:
            return

        tasks = self._tasks[user_id]
        if description:
            description = description.strip()
            for task in tasks:
                if task["description"] == description:
                    task["completed"] = True
        else:
            for task in tasks:
                task["completed"] = True


memory = AgentMemory()
