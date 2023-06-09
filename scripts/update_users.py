# Import modules from parent folder
import os
import sys
PARENT_FODLER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PARENT_FODLER)

from datetime import datetime, timedelta
from database import DataBase
from tools import date_iso

db_path = os.path.join(PARENT_FODLER,  "bot.db")

# --- UPDATE THIS VARIABLE TO CHANGE USER STATUS AND DATE ---
STATUS = "followed" # New status. values: to follow, followed, unfollowed, followed back, blocked
DAYS_BACK = 3 # Last change date. 0 = today, 1 = yesterday, 2 = the day before yesterday, etc.

today = datetime.now()
today = today.replace(hour=0, minute=0, second=0, microsecond=0)
to_date = today - timedelta(days=DAYS_BACK)
to_date_iso = date_iso.get_date_iso (to_date)

# Select all registers from bot table
database = DataBase()
users = database.get_users ()

for user in users:
    user_name = user[0]
    database.update_user (user_name, STATUS, to_date_iso)