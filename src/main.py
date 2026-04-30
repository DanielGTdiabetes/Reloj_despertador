import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import AlarmClockApp


if __name__ == "__main__":
    AlarmClockApp().run()

