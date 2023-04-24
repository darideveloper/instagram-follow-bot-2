import os
import sqlite3
from tools import date_iso

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))

class DataBase ():
    
    def __init__ (self): 
        """ Connect with database """
        
        # Connect with database
        db_path = os.path.join(CURRENT_FOLDER, f"bot.db")
        self.conn = sqlite3.connect(db_path)
        
        # Create db on start
        self.__create_databse__()
        
    def __create_databse__ (self):
        """ Create tables 'users' and 'settings' in database, with default values
        """
        
        self.run_sql ("CREATE TABLE IF NOT EXISTS users (user char, status char, date char, message char DEFAULT '')")
        self.run_sql ("CREATE TABLE IF NOT EXISTS settings (name char, value char)")
        
        # Create default status to "follow"
        status = self.run_sql ("select value from settings where name = 'status' ")
        if not status:
            self.run_sql ("INSERT INTO settings (name, value) VALUES ('status', 'follow') ON CONFLICT DO NOTHING")
        
    def run_sql (self, sql:str):
        """ Run sql command

        Args:
            sql (str): sql command

        Returns:
            data: sql returned data (if exist)
            
        """
        
        # Get cursor
        cur = self.conn.cursor()
        
        # Ren sql and get data if exists
        res = cur.execute(sql)
        data = res.fetchall()
        
        # Commit changes
        self.conn.commit()
        
        # Return data if exists
        if data:
            return data
        
    def delete_users (self):
        """ Delete all registers from 'users' table
        """
        
        self.run_sql ("delete from users")
        
    
    def get_users (self, status:str="") -> list:
        """ Get users from database, filtering by status if needed

        Args:
            status (str, optional): Status of the users to select. Defaults to "".

        Returns:
            list: users data
        """
        
        if status:
            users = self.run_sql (f"select * from users users where status = '{status}' ")
        else:
            users = self.run_sql ("select * from users")
        
        if users:
            return users
        else:
            return []
        
    def count_users (self, status:str="") -> int:
        """ Get user with specific status

        Args:
            status (str, optional): Status of the users to count. Defaults to "".

        Returns:
            int: number of users found
        """
        
        if status:
            return self.run_sql (f"SELECT COUNT(user) FROM users WHERE status = '{status}'")[0][0]
        else:
            return self.run_sql (f"SELECT COUNT(user) FROM users")[0][0]
    
    def insert_user (self, user:str, status:str="to follow", date:str=date_iso.get_today_iso ()):
        """ Insert new user in users table

        Args:
            user (str): user name
            status (str, optional): current status. Defaults to "to follow".
            date (str, optional): new date. Defaults to date_iso.get_today_iso ().
        """
        
        today_str = date_iso.get_today_iso ()
        self.run_sql (f"INSERT INTO users VALUES ('{user}', '{status}', '{date}', '')")
        
    def update_user (self, user:str, status:str, date:str=date_iso.get_today_iso ()):
        """ Update user status

        Args:
            user (str): user name
            status (str): new status
            date (str, optional): new date. Defaults to date_iso.get_today_iso ().
        """
        
        self.run_sql (f"UPDATE users SET status = '{status}', date = '{date}' WHERE user = '{user}'")
    
    def get_status (self) -> str:
        """ Get current bot status
        
        Returns:
            str: bot status
        """
        
        # Get bot status
        status = self.run_sql ("select value from settings where name = 'status' ")[0][0]
        
        return status
    
    def set_status (self, status:str):
        """ Set bot status
        
        Args:
            status (str): new bot status
        """
        
        # Set bot status
        self.run_sql (f"update settings set value = '{status}' where name = 'status'")
        
    def set_message (self, user:str, message:str):
        """ Save message sent to users

        Args:
            user (str): user name
            message (str): message body
        """
        
        self.run_sql (f"update users set message = '{message}' where user = '{user}'")