# Import modules from parent folder
import os
import sys
parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_folder)

from bot import Bot

try:
    bot_instance = Bot()
    bot_instance.auto_run ()
except Exception as err:
    print (f"Error: bot stopped. Details: {err}")
    input ("Press Enter to exit...")