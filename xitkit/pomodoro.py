"""
A Pomodoro Timer App using Textual.
A work session is followed by a break session.

"""




from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header, Static, Label
from datetime import datetime, timedelta
import click


class Timer:
    """Handles all timer logic for work and break sessions."""
    
    def __init__(self, work_minutes=25, break_minutes=5):
        self.work_duration = work_minutes * 60 + 1 # Convert to seconds
        self.break_duration = break_minutes * 60 + 1
        self.reset()
    
    def reset(self):
        """Reset timer to initial state."""
        self.is_work_session = True
        self.is_running = True
        self.start_time = datetime.now()
        self.paused_elapsed = 0  # Time elapsed before current pause
    
    def pause(self):
        """Pause the timer and store elapsed time."""
        if self.is_running:
            self.paused_elapsed += self._get_current_elapsed()
            self.is_running = False
    
    def resume(self):
        """Resume the timer from pause."""
        if not self.is_running:
            self.start_time = datetime.now()
            self.is_running = True
    
    def toggle_pause(self):
        """Toggle between pause and resume."""
        if self.is_running:
            self.pause()
        else:
            self.resume()
    
    def finish_session(self):
        """Finish current session early and switch to next."""
        self.is_work_session = not self.is_work_session
        self.start_time = datetime.now()
        self.paused_elapsed = 0
        self.is_running = True
    
    def _get_current_elapsed(self):
        """Get elapsed time since start_time."""
        if not self.is_running:
            return 0
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_total_elapsed(self):
        """Get total elapsed time including paused time."""
        return self.paused_elapsed + self._get_current_elapsed()
    
    def get_remaining_time(self):
        """Get remaining time in current session."""
        session_duration = self.work_duration if self.is_work_session else self.break_duration
        total_elapsed = self.get_total_elapsed()
        remaining = session_duration - total_elapsed
        
        # Check if session should switch (only when running)
        if self.is_running and remaining <= 0:
            self._switch_session()
            remaining = self.work_duration if self.is_work_session else self.break_duration
        
        return max(0, remaining)
    
    def _switch_session(self):
        """Switch between work and break sessions."""
        self.is_work_session = not self.is_work_session
        self.start_time = datetime.now()
        self.paused_elapsed = 0
    
    def get_session_type(self):
        """Get current session type as string."""
        return "Work Session" if self.is_work_session else "Break Session"
    
    def format_time(self, seconds):
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

# ASCII art for digits 0-9 and colon
ASCII_DIGITS = {
    '0': [
        "██████",
        "██  ██",
        "██  ██",
        "██  ██",
        "██████"
    ],
    '1': [
        "    ██",
        "    ██",
        "    ██",
        "    ██",
        "    ██"
    ],
    '2': [
        "██████",
        "    ██",
        "██████",
        "██    ",
        "██████"
    ],
    '3': [
        "██████",
        "    ██",
        "██████",
        "    ██",
        "██████"
    ],
    '4': [
        "██  ██",
        "██  ██",
        "██████",
        "    ██",
        "    ██"
    ],
    '5': [
        "██████",
        "██    ",
        "██████",
        "    ██",
        "██████"
    ],
    '6': [
        "██████",
        "██    ",
        "██████",
        "██  ██",
        "██████"
    ],
    '7': [
        "██████",
        "    ██",
        "    ██",
        "    ██",
        "    ██"
    ],
    '8': [
        "██████",
        "██  ██",
        "██████",
        "██  ██",
        "██████"
    ],
    '9': [
        "██████",
        "██  ██",
        "██████",
        "    ██",
        "██████"
    ],
    ':': [
        "      ",
        "  ██  ",
        "      ",
        "  ██  ",
        "      "
    ],
    ' ': [
        "      ",
        "      ",
        "      ",
        "      ",
        "      "
    ]
}

def create_large_text(text):
    """Create ASCII art representation of the given text."""
    lines = [""] * 5
    for char in text:
        char_lines = ASCII_DIGITS.get(char, ASCII_DIGITS[' '])
        for i in range(5):
            lines[i] += char_lines[i] + "  "  # Add spacing between characters
    return "\n".join(lines)




class PomodoroApp(App):
    """A Textual Pomodoro Timer """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),
                ("r", "reset_session", "Reset Session"),
                ("p", "pause_session", "Pause Session"),
                ("f", "finish_session", "Finish current Session")]

    def __init__(self, **kwargs):
        self.time_work = kwargs.pop("time_work", 25)
        self.time_break = kwargs.pop("time_break", 5)
        self.timer = Timer(self.time_work, self.time_break)
        super().__init__(**kwargs)

    CSS = """
    Screen {
        align: center middle;
        layout: vertical;
        background: black;
    }
    Screen.break-session {
        background: #1a2f1a;
    }
    #clock {
        width: auto;
        height: auto;
        text-align: center;
        content-align: center middle;
        color: cyan;
        text-opacity: 100%;
        margin-bottom: 1;
    }
    #clock.break-session {
        color: #90ee90;
    }
    #clock.paused {
        text-opacity: 30%;
    }
    #status-label {
        width: auto;
        height: 1;
        text-align: center;
        content-align: center middle;
        color: yellow;
        text-style: italic;
    }
    #status-label.break-session {
        color: #98fb98;
    }
    Static {
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Static("", id="clock")
        yield Label("", id="status-label")
    
    def on_ready(self) -> None:
        self.title = f"Pomodoro Timer - {self.timer.get_session_type()}"
        self.update_clock()
        self.set_interval(1, self.update_clock)

    def update_clock(self) -> None:
        clock = self.query_one("#clock", Static)
        status_label = self.query_one("#status-label", Label)
        screen = self.screen
        
        # Get remaining time from timer
        remaining_seconds = self.timer.get_remaining_time()
        
        # Set colors based on session type
        is_break = not self.timer.is_work_session
        if is_break:
            screen.add_class("break-session")
            clock.add_class("break-session")
            status_label.add_class("break-session")
        else:
            screen.remove_class("break-session")
            clock.remove_class("break-session")
            status_label.remove_class("break-session")
        
        # Set opacity based on running state and update status label
        if not self.timer.is_running:
            clock.add_class("paused")
            status_label.update("(paused) - Press 'p' to continue")
        else:
            clock.remove_class("paused")
            status_label.update("")  # Empty during normal operation
            
        # Update title if session changed
        current_session = self.timer.get_session_type()
        if self.title != f"Pomodoro Timer - {current_session}":
            self.title = f"Pomodoro Timer - {current_session}"
        
        # Format and display time
        time_display = self.timer.format_time(remaining_seconds)
        clock.update(create_large_text(time_display))

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_reset_session(self) -> None:
        """Reset the timer to the beginning."""
        self.timer.reset()
        self.title = f"Pomodoro Timer - {self.timer.get_session_type()}"
        self.update_clock()

    def action_pause_session(self) -> None:
        """Toggle pause/resume of the current session."""
        self.timer.toggle_pause()
        self.update_clock()

    def action_finish_session(self) -> None:
        """Finish current session early and switch to the next one."""
        self.timer.finish_session()
        self.title = f"Pomodoro Timer - {self.timer.get_session_type()}"
        self.update_clock()

@click.command()
@click.argument('time_work', type=int, default=25)
@click.argument('time_break', type=int, default=5)
def main(time_work: int, time_break: int) -> None:
    """Run the Pomodoro Timer App."""
    app = PomodoroApp(time_work=time_work, time_break=time_break)
    app.run()

if __name__ == "__main__":
    main()