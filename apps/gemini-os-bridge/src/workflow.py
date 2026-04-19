import json
import os
import time

class WorkflowManager:
    def __init__(self, state_file="workflow_state.json"):
        self.state_file = state_file
        self.state = {
            "current_step": 0,
            "tasks": [],
            "context": {},
            "status": "idle"
        }
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                self.state = json.load(f)

    def save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=4, ensure_ascii=False)

    def set_tasks(self, tasks):
        self.state["tasks"] = tasks
        self.state["current_step"] = 0
        self.state["status"] = "running"
        self.save_state()

    def add_task_at(self, index, task):
        self.state["tasks"].insert(index, task)
        self.save_state()

    def remove_task_at(self, index):
        if 0 <= index < len(self.state["tasks"]):
            del self.state["tasks"][index]
            self.save_state()

    def get_next_task(self):
        if self.state["current_step"] < len(self.state["tasks"]):
            task = self.state["tasks"][self.state["current_step"]]
            return task
        return None

    def complete_step(self, result=None):
        if result:
            step_name = self.state["tasks"][self.state["current_step"]]["name"]
            self.state["context"][step_name] = result
        self.state["current_step"] += 1
        self.save_state()

    def pause(self, reason="User intervention required"):
        self.state["status"] = "paused"
        self.state["pause_reason"] = reason
        self.save_state()
        print(f"\n[PAUSED] {reason}")

    def resume(self):
        self.state["status"] = "running"
        self.save_state()
