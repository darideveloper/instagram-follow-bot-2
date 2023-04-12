# Import modules from parent folder
import os
import sys
PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_FODLER)

from database import DataBase

# Select all registers from bot table
database = DataBase("bot")
status = database.run_sql ("select value from settings where name = 'status' ")[0][0]
print (status)
