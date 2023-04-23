import os
import sqlite3

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))

class DataBase ():
    
    def __init__ (self): 
        """ Connect with database """
        
        # Connect with database
        db_path = os.path.join(CURRENT_FOLDER, f"bot.db")
        self.conn = sqlite3.connect(db_path)
        
        # Create bot table if not exists
        self.run_sql ("")
        
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
        
    
    def get_users (self) -> list:
        """ Get all users from database
        """
        
        return self.run_sql ("select * from users")
    
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