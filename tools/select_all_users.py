# Import modules from parent folder
import os
import sys
PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_FODLER)

from database import DataBase

db_path = os.path.join(PARENT_FODLER,  "bot.db")

# Select all registers from bot table
database = DataBase("bot")
registers = database.run_sql ("select * from users")
if registers:
    for register in registers:
        print (register)
