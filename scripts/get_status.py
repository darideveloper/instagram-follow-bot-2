# Import modules from parent folder
import os
import sys
PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_FODLER)

from database import DataBase

# Select all registers from bot table
database = DataBase()
status = database.get_status ()
print (status)
