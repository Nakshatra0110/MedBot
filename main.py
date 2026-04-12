"""
AI Health Chatbot - Unified Entry Point
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.healthbot_frame import HealthBotApp

if __name__ == "__main__":
    app = HealthBotApp()
    app.mainloop()
