import os
import json
import time
import random
from dotenv import load_dotenv
from database import DataBase
from selenium.webdriver.common.by import By
from scraping_manager.automate import WebScraping
from datetime import datetime, timedelta
from tools import date_iso

class Bot (WebScraping):
    
    def __init__ (self):
        """ Constructor of class
        """
        
        # Load environment variables
        load_dotenv ()
        
        # paths
        self.project_folder = os.path.dirname (__file__)
        self.proxies_path = os.path.join (self.project_folder, "proxies.json")
        self.cookies_path = os.path.join (self.project_folder, "cookies.json")
        
        # Get proxy
        self.proxy = self.__get_random_proxy__ ()
        
        # Read environment variables
        self.headless = False
        self.target_users = os.getenv ("target_users").split(",")
        self.max_follow = int (os.getenv ("max_follow", 0))
        self.chrome_folder = os.getenv ("chrome_folder", "")
        self.days_block = int (os.getenv ("days_block", 0))
        
        # History file
        self.history_file = os.path.join (os.path.dirname (__file__), "history.csv")
        
        # pages / urls
        self.url_instagram = "https://www.instagram.com/"
        
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
            
            "users_followers": '.x7r02ix.xf1ldfh.x131esax ._aano > div:first-child .xt0psk2 > .xt0psk2 > a',
            "users_followers_wrapper": '[role="dialog"] ._aano',
            "users_followers_load_more": "",
            
            "follow_btn": "header button._acan._acap._acas._aj1-",
            "like_btn": "span:first-child button._abl-",
            
            "unfollow_btn": "header button._acan._acap._aj1-", 
            "unfollow_confirm_btn": '.x1cy8zhl .x9f619 > div[role="button"]:last-child',
            "unfollow_confirm_btn_b": '.x1n2onr6.xzkaem6 .x78zum5.xdt5ytf > button',
            
            "bot_profile": '.xh8yej3.x1iyjqo2 > div:last-child [role="link"]',
            
            "more_actions_btn": "button._abl-",
            "block_btn": "._a9-v button:first-child",
            "block_confirm_btn": "._a9-v button:first-child",
            
        }
    
        # Start chrome
        super ().__init__ (headless=self.headless, chrome_folder=self.chrome_folder, 
                           start_killing=True, web_page=self.url_instagram,
                           proxy_server=self.proxy["host"], proxy_port=self.proxy["port"], 
                           proxy_user=self.proxy["user"], proxy_pass=self.proxy["password"],
                           cookies_path=self.cookies_path)
        
        # Conneact with database and create tables
        self.database = DataBase()
    
    def __get_random_proxy__ (self) -> dict:
        """ Get random proxy from 'proxies.json' file

        Returns:
            dict: proxy data: user, password, host, port
        """
        
        # read proxies
        with open (self.proxies_path, "r") as file:
            proxies = json.load (file)
            
        # Select random proxy
        proxy = random.choice (proxies)
        
        return proxy     
    
    def __wait__ (self, message:str=""):
        """ Wait time and show message

        Args:
            message (str, optional): message to show after wait time. Defaults to "".
        """
        
        time.sleep (random.randint(30, 180))
        if message:
            print (message)
    
    def __get_profiles__ (self, selector_link:str, selector_wrapper:str, load_more_selector:str, 
                        scroll_by:int, max_users:int) -> list: 
        """ get links from scrollable element

        Args:
            selector_link (str): css selector of the link
            selector_wrapper (str): css selector of the scroll element
            load_more_selector (str): Selector of button for load more links.
            scroll_by (int): number of pixels to scroll down
            max_users (int): max number of links to get
            
        Returns:
            list: list of links found
        """
                                
        # Get users from database already followerd
        users_followed = self.database.get_users (status="followed")
        users_unfollowed = self.database.get_users (status="unfollowed")
        skip_users_data = users_followed + users_unfollowed
        if not skip_users_data:
            skip_users_data = []
        skip_users = list(map(lambda user: user[0], skip_users_data))
        
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
            
    def __set_page_wait__ (self, user:str):
        """ Open user profile and wait for load

        Args:
            user (str): user link
        """
        self.set_page (user)
        time.sleep (10)
        self.refresh_selenium ()
        
    def __get_post__ (self, max_post = 100): 
        """
        Get the post links of the current user
        """
                
        # Get number of post of the user 
        post_links = self.get_attribs(self.selectors["post"], "href")
        if len(post_links) > max_post: 
            post_links = post_links[:max_post]

        return post_links
        
    def __follow_like_users__ (self, max_posts:int=3):
        """ Follow and like posts of users from a profile_links

        Args:
            max_posts (int, optional): number of post to like. Defaults to 3.
        """
        
        print ("\nStart following and liking users...")
        
        # Get users to follow from database
        users_data = self.database.get_users (status="to follow")
        users = list(map(lambda user_data: user_data[0], users_data))
        
        for user in users:
            
            print (f"User {users.index(user) + 1} / {len(users)}: {user}")
            
            # Set user page1
            self.__set_page_wait__ (user)
            
            # Follow user
            follow_text = self.get_text (self.selectors["follow_btn"])
            if follow_text and follow_text.lower().strip() == "follow":
                self.click_js (self.selectors["follow_btn"])
                self.__wait__ (f"\tuser followed: {user}")
            else:
                self.__wait__ (f"\tuser already followed")
            
            # Get number of post of the user 
            post_links = self.__get_post__ (max_posts)
            
            # Like each post (the last three)
            for post_link in post_links: 
                
                self.__set_page_wait__ (post_link)
                self.refresh_selenium ()
                
                # Get like title text
                like_title_selector = self.selectors["like_btn"] + " svg"
                like_title = self.get_attrib (like_title_selector, "aria-label")
                
                if like_title and like_title.lower().strip() == "like":
                
                    try:
                        self.click_js(self.selectors["like_btn"])
                    except:
                        print (f"\tpost {post_links.index(post_link) + 1} / {max_posts} skiped (like button not found))")
                    else:
                        self.__wait__ (f"\tpost {post_links.index(post_link) + 1} / {max_posts} liked")
                        
                else:
                    print (f"\tpost {post_links.index(post_link) + 1} / {max_posts} skiped (already liked)")
                        
            # Update status of the user in database
            self.database.update_user (user, "followed")
    
    def __get_users_posts__ (self, target_user:str, max_users:int) -> list:
        """ Load user to follow from target posts comments and likes
        
        Args:
            target_user (str): user target to get followers
            max_users (int): max users to follow from target

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
            profile_links += self.__get_profiles__ (
                self.selectors["users_posts_likes"], 
                self.selectors["users_posts_likes_wrapper"], 
                self.selectors["users_posts_likes_load_more"],
                scroll_by=2000,      
                max_users=int(max_users/2) + 1,
            )
            
            # Open post comments
            self.__set_page_wait__ (post_link)
            
            # Go down and get profiles links from comments
            profile_links += self.__get_profiles__ (
                self.selectors["users_posts_comments"], 
                self.selectors["users_posts_comments_wrapper"], 
                self.selectors["users_posts_comments_load_more"], 
                scroll_by=4000,
                max_users=int(max_users/2) + 1,
            )
            
            # End loop if max users reached
            if len(profile_links) >= max_users:
                profile_links = profile_links[:max_users]
                break
        
        print (f"\t\t{len(profile_links)} users found")
        
        return profile_links

    def __get_users_followers__ (self, target_user:str, max_users:int) -> list:
        """Load user to follow from target current followers

        Args:
            target_user (str): user target to get followers
            max_users (int): max users to follow from target

        Returns:
            list: list of users found
        """
        
                        
        print (f"\tgetting from followers list...")
        
        # Show followers page 
        url = f"https://www.instagram.com/{target_user}/followers/"
        self.set_page (url)
                
        # Go down and get profiles links
        profile_links = self.__get_profiles__ (
            self.selectors["users_followers"], 
            self.selectors["users_followers_wrapper"], 
            self.selectors["users_followers_load_more"],
            scroll_by=2000,
            max_users=max_users,
        )
                    
        print (f"\t\t{len(profile_links)} users found")
    
        return profile_links
    
    def follow (self):
        """ Follow users from list of target users
        """
        
        print ("\n-----------------------------")
        print ("FOLLOWING USERS:")
        print ("-----------------------------")
        
        # Count user to follow or followed already in database
        users_to_follow_num = self.database.count_users ("to follow")
        users_followd_num = self.database.count_users ("followed")
        
        if users_followd_num > 0:
            print (f"Users already followed: {users_followd_num}")
        
        # Calculate users to follow from each target user
        remaining_users = self.max_follow - users_to_follow_num - users_followd_num
        max_follow_target = int(remaining_users / len(self.target_users))
        
        if remaining_users > 0:
            print (f"Users to follow: {remaining_users}")
        
        if max_follow_target > 0:
            print (f"Max users to follow from each target: {max_follow_target}")
        
            total_users_found = 0
            for target_user in self.target_users:
                
                users_found = []
                print (f"\nGetting users from: {target_user}")
                
                # Get users from target posts
                max_follow_comments = int(max_follow_target/2)
                users_posts = self.__get_users_posts__ (target_user, max_follow_comments)
                users_found += users_posts
                
                # Get users from target followers
                max_follow_followers = max_follow_target - len(users_found)
                users_followers = self.__get_users_followers__ (target_user, max_follow_followers)
                users_found += users_followers    
                
                print (f"\t{len(users_found)} users found from {target_user}")       
                    
                # Save users in database
                print (f"\tSaving users in database...")    
                for user in users_found:
                    self.database.insert_user (user)
                    
                    
                total_users_found += len(users_found)
                
        users_to_follow_num = self.database.count_users ("to follow")
        print (f"\n{users_to_follow_num} users ready to follow")
        
        if users_to_follow_num > 0:
            self.__follow_like_users__ ()
        
        print ("Done.")
     
    def unfollow (self):
        """ Unfollow users already followed
        """
        
        print ("\n-----------------------------")
        print ("UNFOLLOW USERS:")
        print ("-----------------------------")
        
        # Select users to unfollow
        unfollow_users_data = self.database.get_users ('followed')
        if unfollow_users_data:
            unfollow_users = list(map(lambda user: user[0], unfollow_users_data))
            unfollow_users_num = len(unfollow_users)
        else:
            unfollow_users = []
            unfollow_users_num = 0
        
        # Fix unfollow usersut
        if unfollow_users_num > self.max_follow:
            unfollow_users = unfollow_users[:self.max_follow]
        
        print (f"{unfollow_users_num} users to unfollow")
        
        # Unfollow each user
        for user in unfollow_users:
            
            # Load user page
            self.__set_page_wait__ (user)
            
            # Unfollow user
            unfollow_text = self.get_text (self.selectors["unfollow_btn"])
            if unfollow_text.lower().strip() in ["following", "requested"]:    
                self.click_js (self.selectors["unfollow_btn"])
                self.refresh_selenium ()
                
                # Confirm unfollow
                unfollow_button = self.get_elems (self.selectors["unfollow_confirm_btn"])
                if unfollow_button:
                    self.click_js (self.selectors["unfollow_confirm_btn"])
                else:
                    self.click_js (self.selectors["unfollow_confirm_btn_b"])
                
                # Update user status in database
                self.database.update_user (user, "unfollowed")
                
                self.__wait__ (f"\t{user} unfollowed")
            else:
                self.__wait__ (f"\t{user} already unfollowed (or blocked)")
                
    def block (self):
        """ Block users already followed who didn't follow back in three days
        """
        
        print ("\n-----------------------------")
        print ("BLOCKING USERS:")
        print ("-----------------------------")
        
        # Get follors of the bot
        self.set_page (self.url_instagram)
        
        # Open bot profile page
        bot_profile = self.get_attrib (self.selectors["bot_profile"], "href")
        if not bot_profile:
            raise Exception ("bot profile not found")
        
        # Open followers page
        followes_page = bot_profile + "followers"
        self.set_page (followes_page)
        
        # Go down and get profiles links
        followers = self.__get_profiles__ (
            self.selectors["users_followers"], 
            self.selectors["users_followers_wrapper"], 
            self.selectors["users_followers_load_more"],
            scroll_by=2000,
            max_users=9999,
        )
        
        print (f"\t{len(followers)} followers found")
        
        # Get users already followed
        uers_followed = self.database.get_users (status="followed")
        print (f"\tChecking {len(uers_followed)} users already followed...")
        
        # Filter with followed date
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        date_days_back = today - timedelta(days=self.days_block)
        users_to_block = list(filter(lambda user:  date_iso.get_date_from_iso(user[2]) <= date_days_back, uers_followed))
        
        # Get user names
        users_to_block = list(map(lambda user: user[0], users_to_block))
        
        if not users_to_block:
            print ("\tNo users to block")
            return ""
        
        if users_to_block:
            # Block users who no returned the follow
            print (f"\t{len(users_to_block)} users found to block")
            print ("\tBlocking users...")
            
            for user in users_to_block:
                self.__set_page_wait__ (user)
                
                # Check user status
                unfollow_text = self.get_text (self.selectors["unfollow_btn"])
                if unfollow_text.lower().strip() == "unblock":
                    # Skip user
                    print (f"\t{user} already blocked")
                else:  
                    # Block user
                    self.click_js (self.selectors["more_actions_btn"])
                    self.refresh_selenium ()
                    
                    self.click_js (self.selectors["block_btn"])
                    self.refresh_selenium ()
                    
                    self.click_js (self.selectors["block_confirm_btn"])
                    self.refresh_selenium ()
                    
                    # Update user status in database
                    
                    print (f"\t{user} blocked") 
                    
                self.database.update_user (user, "blocked")
        
        return None
                
    def auto_run (self):
        """ Run auto_follow and auto_unfollow functions in loop, using status from database
        """
        
        while True:
        
            # get status from database
            status = self.database.get_status ()
            
            # Run follow or unfollow based in status from database
            if status == "follow":
                self.follow ()
                self.database.set_status ("unfollow")
            elif status == "unfollow":
                self.unfollow ()
                self.database.set_status ("follow")       
    