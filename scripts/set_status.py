# Import modules from parent folder
import os
import sys
PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_FODLER)

from database import DataBase

# Select all registers from bot table
STATUS = "unfollow"
database = DataBase()
database.set_status (STATUS)
