import sqlite3

class DataBase ():
    
    def __init__ (self, db_name:str): 
        """ Connect with database """
        
        # Connect with database
        self.conn = sqlite3.connect(f"{db_name}.db")
        
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
        