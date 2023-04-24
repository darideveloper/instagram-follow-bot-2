# Import modules from parent folder
import os
import sys
PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_FODLER)

from database import DataBase

# --- UPDATE THIS VARIABLE TO CHANGE THE STATUS ---
STATUS = "follow" # values: follow, unfollow, block

# Select all registers from bot table
database = DataBase()
database.set_status (STATUS)
