# Placeholder for Time System
# This system will manage the AI's perception and use of time, scheduling, reminders, etc.

import datetime

class TimeSystem:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.current_time_override = None # For testing or specific scenarios
        self.reminders = []
        print("TimeSystem initialized.")

    def get_current_time(self) -> datetime.datetime:
        """Returns the current datetime."""
        if self.current_time_override:
            return self.current_time_override
        return datetime.datetime.now()

    def get_formatted_current_time(self, time_format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Returns the current time formatted as a string."""
        return self.get_current_time().strftime(time_format)

    def set_reminder(self, time_expression: str, event_description: str) -> bool:
        """
        Sets a reminder based on a time expression (e.g., "in 5 minutes").
        """
        parts = time_expression.lower().split()
        if len(parts) == 3 and parts[0] == "in" and parts[2] in ["minute", "minutes"]:
            try:
                minutes = int(parts[1])
                due_time = self.get_current_time() + datetime.timedelta(minutes=minutes)
                self.reminders.append({"due_time": due_time, "description": event_description})
                print(f"TimeSystem: Reminder set for '{event_description}' at {due_time}.")
                return True
            except ValueError:
                print(f"TimeSystem: Could not parse time expression: {time_expression}")
                return False

        print(f"TimeSystem: Time expression not supported: {time_expression}")
        return False

    def check_due_reminders(self) -> list:
        """
        Checks for any reminders that are due.
        Returns a list of due reminder descriptions and removes them from the list.
        """
        now = self.get_current_time()
        due_reminders = [r for r in self.reminders if r["due_time"] <= now]
        self.reminders = [r for r in self.reminders if r["due_time"] > now]
        return [r["description"] for r in due_reminders]

    def get_time_of_day_segment(self) -> str:
        """
        Determines the current time of day segment.
        Returns "morning", "afternoon", "evening", or "night".
        """
        current_hour = self.get_current_time().hour
        if 5 <= current_hour < 12:
            return "morning"
        elif 12 <= current_hour < 18:
            return "afternoon"
        elif 18 <= current_hour < 22:
            return "evening"
        else: # 22:00 to 04:59
            return "night"

if __name__ == '__main__':
    time_sys = TimeSystem()

    current_time_str = time_sys.get_formatted_current_time()
    print(f"Current formatted time: {current_time_str}")

    time_segment = time_sys.get_time_of_day_segment()
    print(f"Current time segment: {time_segment}")

    time_sys.set_reminder("in 10 minutes", "Check on the AI's learning progress.")

    due_reminders = time_sys.check_due_reminders()
    if not due_reminders: # Corrected variable name
        print("No reminders currently due.")
    else:
        print(f"Due reminders: {due_reminders}")
