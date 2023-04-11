import os
import csv
import time
import random
import config
from database import DataBase
from selenium.webdriver.common.by import By
from scraping_manager.automate import WebScraping

class Bot (WebScraping):
    
    def __init__ (self):
        """ Constructor of class
        """
        
        # Read credentials
        self.debug = config.get_credential ("debug")
        self.headless = config.get_credential ("headless")
        self.list_follow = config.get_credential ("list_follow")
        self.max_follow = config.get_credential ("max_follow")
        self.chrome_folder = config.get_credential ("chrome_folder")
        
        # History file
        self.history_file = os.path.join (os.path.dirname (__file__), "history.csv")
        
        # Css selectors
        self.selectors = {
            "post": "._ac7v._al3n ._aabd._aa8k._al3l a",
            "show_post_likes": "span.x1lliihq > a",
            "users_posts_likes": "span.x1lliihq.x193iq5w.x6ikm8r a",
            "users_posts_likes_wrapper": '[role="dialog"] [style^="height: 356px;"]',
            "users_posts_likes_load_more": "",
            "users_posts_comments": "._ae2s._ae3v._ae3w .xt0psk2 > a",
            "users_posts_comments_wrapper": "._ae2s._ae3v._ae3w .x78zum5.xdt5ytf.x1iyjqo2.x9ek82g",
            "users_posts_comments_load_more": "",
            "users_followers": ".x7r02ix.xf1ldfh.x131esax .xt0psk2 > .xt0psk2 > a",
            "users_followers_wrapper": '[role="dialog"] ._aano',
            "users_followers_load_more": "",
        }
    
        # Start chrome
        super ().__init__ (headless=self.headless, chrome_folder=self.chrome_folder, start_killing=True)
        
        # Conneact with database and create tables
        self.database = DataBase("bot")
        self.database.run_sql ("CREATE TABLE IF NOT EXISTS users (user char, status char)")
        self.database.run_sql ("CREATE TABLE IF NOT EXISTS status (status char)")
    
    def __wait__ (self, message:str=""):
        """ Wait time and show message

        Args:
            message (str, optional): message to show after wait time. Defaults to "".
        """
        
        time.sleep (random.randint(30, 180))
        if message:
            print (message)
    
    def __load_links__ (self, selector_link:str, selector_wrapper:str, load_more_selector:str, 
                        scroll_by:int, max_users:int, skip_users:list) -> list: 
        """ get links from scrollable element

        Args:
            selector_link (str): css selector of the link
            selector_wrapper (str): css selector of the scroll element
            load_more_selector (str): Selector of button for load more links.
            scroll_by (int): number of pixels to scroll down
            max_users (int): max number of links to get
            skip_users (list): list of users to skip
            
        Returns:
            list: list of links found
        """
                                
        # TODO: get already followed from database
        
        more_links = True
        links_found = []
        last_links = []
        while more_links: 
            
            # Get all profile links
            time.sleep(6)
            self.refresh_selenium()
            links = self.get_attribs(selector_link, "href", allow_duplicates=False, allow_empty=False)
            
            # Break where no new links
            if links == last_links: 
                break
            else: 
                last_links = links
            
            # Validate each link
            for link in links: 
                
                # Save current linl
                if link not in skip_users and link not in links_found: 
                    links_found.append(link)
                    
                # Count number of links
                links_num = len (links_found)
                if links_num >= max_users: 
                    more_links = False
                    break
            
            # Go down
            elems = self.get_elems (selector_wrapper)
            if elems:
                self.driver.execute_script(f"arguments[0].scrollBy (0, {scroll_by});", elems[0])
            
            # Click button for load more results
            if load_more_selector:
                elems = self.get_elems (load_more_selector)
                if elems:
                    self.click_js (load_more_selector)
                    time.sleep(3)
        
        # Fix number of links found
        if len (links_found) > max_users: 
            links_found = links_found[:max_users]
        
        return links_found
    
    def __save_user_history__ (self, user:str, status:str):
        """ Save new user in history file

        Args:
            user (str): user link
            status (str): status of the user
        """
        
        with open (self.history_file, "a", newline='') as file:
            csv_writer = csv.writer (file)
            csv_writer.writerow ([user, status])
            
    def __set_page_wait__ (self, user:str):
        """ Open user profile and wait for load

        Args:
            user (str): user link
        """
        self.set_page (user)
        time.sleep (10)
        self.refresh_selenium ()
        
    def __follow_like_users__ (self, max_posts:int=3):
        """ Follow and like posts of users from a profile_links

        Args:
            max_posts (int, optional): number of post to like. Defaults to 3.
        """
        
        print ("\nStart following and liking users...")
        
        # Get users to follow from database
        users_data = self.database.run_sql ("SELECT user FROM users WHERE status = 'to follow'")
        users = list(map(lambda user_data: user_data[0], users_data))
        
        for user in users:
            
            # Set user page
            self.__set_page_wait__ (user)
            
            # Follow user
            follow_text = self.get_text (self.selectors["follow"])
            if follow_text.lower().strip() == "follow":
                self.click_js (self.selectors["follow"])
                self.__wait__ (f"user followed: {user}")
            else:
                self.__wait__ (f"user already followed: {user}")
            
            # Get posts of user
            posts_elems = self.get_elems (self.selectors["post"])
            if len(posts_elems) > max_posts:
                posts_elems = posts_elems[:max_posts]
            
            # loop posts to like
            for post in posts_elems:
                
                # Like post
                try:
                    like_button = post.find_element(By.CSS_SELECTOR, self.selectors["like"])
                except:
                    continue
                else:
                    like_button.click ()
                        
                    # Wait after like
                    post_index = posts_elems.index(post) + 1
                    self.__wait__ (f"\tpost liked: {post_index}/{max_posts}")
                    
            
    def __get_unfollow_users__ (self) -> list:
        """ Request to the user the list of followed users from text files

        Returns:
            list: list of followed users to unfollow
        """
        
        # Request follow file to user
        manu_options = ["1", "2"]
        while True:
            print ("1. Follow Advanced")
            print ("2. Follow Classic")
            option = input ("Select folloed list, for unfollow: ")
            if option not in manu_options: 
                print ("\nInvalid option")
                continue
            else:
                break
        
        # Select followed list 
        if option == "1": 
            followed = self.followed_advanced
        elif option == "2":
            followed = self.followed_classic
            
        # Remove users already unfollowed
        followed = list(filter(lambda user: user not in self.unfollowed, followed))
        
        return followed
    
    def __get_users_posts__ (self, target_user:str, max_users:int, skip_users:list=[]) -> list:
        """ Load user to follow from target posts comments and likes
        
        Args:
            target_user (str): user target to get followers
            max_users (int): max users to follow from target
            skip_users (list, optional): list of users to skip. Defaults to [].

        Returns:
            list: list of users found
        """
        
        # Show followers page 
        url = f"https://www.instagram.com/{target_user}"
        self.__set_page_wait__ (url)
        
        # Get posts links
        posts_links = self.get_attribs (self.selectors["post"], "href")
        
        # Open each post details
        profile_links = []
        for post_link in posts_links:                
            print (f"\tgetting from post: {post_link}")
            
            self.__set_page_wait__ (post_link)
            
            # Open post likes
            self.click_js (self.selectors["show_post_likes"])
            self.refresh_selenium ()
            
            # Go down and get profiles links from likes
            profile_links += self.__load_links__ (
                self.selectors["users_posts_likes"], 
                self.selectors["users_posts_likes_wrapper"], 
                self.selectors["users_posts_likes_load_more"],
                scroll_by=2000,      
                max_users=int(max_users/2) + 1,
                skip_users=profile_links + skip_users            
            )
            
            # Open post comments
            self.__set_page_wait__ (post_link)
            
            # Go down and get profiles links from comments
            profile_links += self.__load_links__ (
                self.selectors["users_posts_comments"], 
                self.selectors["users_posts_comments_wrapper"], 
                self.selectors["users_posts_comments_load_more"], 
                scroll_by=4000,
                max_users=int(max_users/2) + 1,
                skip_users=profile_links + skip_users  
            )
            
            # End loop if max users reached
            if len(profile_links) >= max_users:
                break
            
        print (f"\t\t{len(profile_links)} users found")
        
        return profile_links

    def __get_users_followers__ (self, target_user:str, max_users:int, skip_users:list=[]) -> list:
        """Load user to follow from target current followers

        Args:
            target_user (str): user target to get followers
            max_users (int): max users to follow from target
            skip_users (list, optional): list of users to skip. Defaults to [].

        Returns:
            list: list of users found
        """
        
                        
        print (f"\tgetting from followers list...")
        
        # Show followers page 
        url = f"https://www.instagram.com/{target_user}/followers/"
        self.set_page (url)
                
        # Go down and get profiles links
        profile_links = self.__load_links__ (
            self.selectors["users_followers"], 
            self.selectors["users_followers_wrapper"], 
            self.selectors["users_followers_load_more"],
            scroll_by=2000,
            max_users=max_users,
            skip_users=skip_users    
        )
            
        print (f"\t\t{len(profile_links)} users found")
    
        return profile_links
    
    def auto_follow (self):
        
        print ("FOLLOWING USERS:\n")
        
        # Calculate users to follow from each target user
        max_follow_target = int(self.max_follow / len(self.list_follow))
        
        total_users_found = 0
        for target_user in self.list_follow:
            
            users_found = []
            print (f"\nGetting users from: {target_user}")
            
            # Get users from target posts
            max_follow_comments = int(max_follow_target/2)
            users_posts = self.__get_users_posts__ (target_user, max_follow_comments, users_found)
            users_found += users_posts
            
            # Get users from target followers
            max_follow_followers = max_follow_target - len(users_found)
            users_followers = self.__get_users_followers__ (target_user, max_follow_followers, users_found)
            users_found += users_followers    
            
            print (f"\t{len(users_found)} users found from {target_user}")       
                 
            # Save users in database
            print (f"\tSaving users in database...")    
            for user in users_found:
                self.database.run_sql (f"INSERT INTO users VALUES ('{user}', 'to follow')")
                
            total_users_found += len(users_found)
            
        print (f"\n{total_users_found} total users found")
        
        self.__follow_like_users__ ()

        
    def unfollow (self):
        """ Unfollow users """
        
        # Select users to unfollow
        unfollow_users = self.__get_unfollow_users__ () 
        
        # Unfollow each user
        for user in unfollow_users:
            
            # Load user page
            self.__set_page_wait__ (user)
            
            # Unfollow user
            unfollow_text = self.get_text (self.selectors["unfollow"])
            if unfollow_text.lower().strip() == "following":
                self.click_js (self.selectors["unfollow"])
                self.refresh_selenium ()
                
                # Confirm unfollow
                self.click_js (self.selectors["confirm_unfollow"])
                
                # Save user in history
                self.__save_user_history__ (user, "unfollowed")
                
                # Wait after unfollow
                self.__wait__ (f"user unfollowed: {user}")
            
            
    