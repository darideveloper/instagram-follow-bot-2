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
        self.wait_message = int(os.getenv ("wait_message", 0)) * 60
        
        # time of the last message
        self.last_message_time = time.time ()
        
        # History file
        self.history_file = os.path.join (os.path.dirname (__file__), "history.csv")
        
        # pages / urls
        self.url_instagram = "https://www.instagram.com/"
        
        # messages pàth
        self.messages_path = os.path.join (self.project_folder, "messages.txt")
        
        # Css selectors
        self.selectors = {
            "post": "._ac7v._al3n ._aabd._aa8k._al3l a",
            "show_post_likes": 'span > a[href$="liked_by/"]',
            
            "users_posts_likes": "span.x1lliihq.x193iq5w.x6ikm8r a",
            "users_posts_likes_wrapper": '[role="dialog"] [style^="height: 356px;"]',
            "users_posts_likes_load_more": "",
            
            "users_posts_comments": "ul._a9ym .xt0psk2 > a",
            "users_posts_comments_wrapper": 'div.x5yr21d > ul._a9z6._a9za',
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
            
            'message_btn': '.x9f619 > [role="button"]',
            "message_textarea": 'textarea',
            "message_submit": '._ab5x .x1i10hfl[role="button"]',            
        }
    
        # Start chrome
        super ().__init__ (headless=self.headless, chrome_folder=self.chrome_folder, 
                           start_killing=True, web_page=self.url_instagram,
                           proxy_server=self.proxy["host"], proxy_port=self.proxy["port"], 
                           proxy_user=self.proxy["user"], proxy_pass=self.proxy["password"],
                           cookies_path=self.cookies_path)
        
        # Conneact with database and create tables
        self.database = DataBase()
        
        # read messages from txt
        self.messages_options = []
        with open (self.messages_path, "r") as file:
            for line in file:
                self.messages_options.append (line.strip())

    
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
                        scroll_by:int, max_users:int, skip_followed:bool=True, skip_unfollowed:bool=True, 
                        skip_blocked:bool=True, skip_followed_back:bool=True) -> list: 
        """ get links from scrollable element

        Args:
            selector_link (str): css selector of the link
            selector_wrapper (str): css selector of the scroll element
            load_more_selector (str): Selector of button for load more links.
            scroll_by (int): number of pixels to scroll down
            max_users (int): max number of links to get
            
            skip_followed (bool, optional): skip users already followed. Defaults to True.
            skip_unfollowed (bool, optional): skip users already unfollowed. Defaults to True.
            skip_blocked (bool, optional): skip users already blocked. Defaults to True.
            skip_followed_back (bool, optional): skip users already followed back. Defaults to True.
            
        Returns:
            list: list of links found
        """
                                
        # Get users from database to skip
        users_followed = []
        users_unfollowed = []
        users_blocked = []
        users_followed_back = []
        if skip_followed:
            users_followed = self.database.get_users (status="followed")
        if skip_unfollowed:
            users_unfollowed = self.database.get_users (status="unfollowed")
        if skip_blocked:
            users_blocked = self.database.get_users (status="blocked")
        if skip_followed_back:
            users_followed_back = self.database.get_users (status="followed back")
            
        # Format target users
        target_users = list(map(lambda user: f"https://www.instagram.com/{user}/", self.target_users))
            
        skip_users_data = users_followed + users_unfollowed + users_blocked + users_followed_back + target_users
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
            scroll_elem = self.get_elems (selector_wrapper)
            if scroll_elem:
                self.driver.execute_script(f"arguments[0].scrollBy (0, {scroll_by});", scroll_elem[0])
            
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
                self.__wait__ (f"\tuser followed")
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
                        print (f"\tpost {post_links.index(post_link) + 1} / {max_posts} skipped (like button not found))")
                    else:
                        self.__wait__ (f"\tpost {post_links.index(post_link) + 1} / {max_posts} liked")
                        
                else:
                    print (f"\tpost {post_links.index(post_link) + 1} / {max_posts} skipped (already liked)")
                        
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
    
    def __get_users_to_messages__ (self) -> list:
        """ Get the list of the followed users who didn't received message yet
        
        Returns:
            list: list of users to message
        """
                
        # Get followed or followed back users
        users = self.database.get_users (status="followed back")
        
        # Filters users who already received message
        users_to_message = list(filter(lambda user: user[3] == "", users))
        
        return users_to_message
    
    def __send_message__ (self) -> bool:
        """ Submit private random message to the next user

        Returns:
            bool: True if there are more users to message available
        """
        
        users_to_message = self.__get_users_to_messages__ ()
        
        # Detect if there is users to message
        if not users_to_message:
            print ("No users to message")
            return False
        
        # Get next user
        user_to_message = users_to_message[0][0]
        print (f"messaging user: {user_to_message}")
        
        # Go to profile
        self.__set_page_wait__ (user_to_message)
        
        # Validate if there is a message button
        message_btn_text = self.get_text (self.selectors["message_btn"])
        if message_btn_text and message_btn_text.strip().lower() == "message":
            self.click_js (self.selectors["message_btn"])
            time.sleep (5)
            self.refresh_selenium ()
        else:
            error = "message button not found"
            print (f"\tskipped ({error})")
            
            # Save error in database
            self.database.set_message (user_to_message, f"error: {error}")
            
            return True
        
        # Write random message 
        random_message = random.choice (self.messages_options)
        self.send_data (self.selectors["message_textarea"], random_message)
        self.refresh_selenium ()
        
        # Submit message
        self.click_js (self.selectors["message_submit"])
        
        # Save message in database
        self.database.set_message (user_to_message, random_message)
        
        # Update last time message sent
        self.last_message_time = time.time ()
        
        print (f"\tmessage sent: {random_message}")
        return True
        
    def follow (self):
        """ Follow users from list of target users
        """
        
        print ("\n-----------------------------")
        print ("FOLLOWING USERS:")
        print ("-----------------------------")
        
        # Count user to follow or followed already in database
        users_to_follow_num = self.database.count_users ("to follow")
        users_followed_num = self.database.count_users ("followed")
        
        if users_followed_num > 0:
            print (f"Users already followed: {users_followed_num}")
        
        # Calculate users to follow from each target user
        remaining_users = self.max_follow - users_to_follow_num
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
            skip_followed=False
        )
        
        print (f"{len(followers)} followers found")
        
        # Get users already followed
        users_followed = self.database.get_users (status="followed")
        print (f"Checking {len(users_followed)} users already followed...")
        
        # Filter with followed date
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        date_days_back = today - timedelta(days=self.days_block)
        users_followed_last_days = list(filter(lambda user:  date_iso.get_date_from_iso(user[2]) <= date_days_back, users_followed))
        users_to_block = list(filter(lambda user: user[0] not in followers, users_followed_last_days))
        
        # format users lists
        users_to_block = list(map(lambda user: user[0], users_to_block))
        users_followed_last_days = list(map(lambda user: user[0], users_followed_last_days))
        
        if not users_to_block:
            print ("No users to block")
            return ""
        
        # Block users who no returned the follow
        print (f"{len(users_to_block)} users found to block")
        print ("Blocking users...")
        
        for user in users_followed_last_days:
            
            # Update statud of the users who followed back
            if user in followers:
                self.database.update_user (user, "followed back")
                continue
                    
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
    
    def messages (self):
        """ Submit messages to all followed or followed back users, in loop until all users are messaged
        """
        print ("\n-----------------------------")
        print ("MESSAGING USERS:")
        print ("-----------------------------")
        
        # Loop for submit messages in loop
        while True:
            self.__send_message__ ()
            more_users = self.__get_users_to_messages__ ()
            if more_users:
                print ("waiting for next message...")
                time.sleep (self.wait_message)
            else:
                break
    
    def auto_run_loop (self):
        """ Run follow and auto_unfollow functions in loop, using status from database
        """
        
        while True:
            # get status from database
            status = self.database.get_status ()
            
            # Run follow or unfollow based in status from database
            if status == "follow":
                self.follow ()
                self.database.set_status ("block")
            elif status == "block":
                self.block ()
                self.database.set_status ("follow")       
                
            # Submit private message to the next user
            next_message_time = self.last_message_time + self.wait_message
            now = time.time ()
            if now > next_message_time:
                
                print ("\n-----------------------------")
                print ("MESSAGING NEXT USER:")
                print ("-----------------------------")
                
                self.__send_message__ ()
                self.last_message_time = now
            
    
    def auto_run_times (self):
        """ Run follow in loop specific time, and when follow ends, the block and the send messages 
        process start
        """
        
        # Request times and convert to int
        running_time = input ("Running time (minutes): ")
        sleep_time = input ("Sleep time (minutes): ")
        if not running_time.isdigit () or not sleep_time.isdigit (): 
            print ("Invalid times. Try again.")
            return ""
        running_time = int (running_time) * 60
        sleep_time = int (sleep_time) * 60
        
        # Calculate times
        start_time = time.time ()
        end_time = start_time + running_time    
        
        while True:
            now = time.time ()
            if now > end_time:
                print ("\nTime limit reached. Starting block and message process: \n")
                
                self.block ()
                self.messages ()
                
                print (f"\nSleeping for {int(sleep_time / 60)} minutes...")
                time.sleep (sleep_time)
                start_time = time.time ()
                end_time = start_time + running_time
                
            remaing_time = end_time - now
            print (f"\nRemaining time {int(remaing_time / 60)} minutes...")                
            
            self.follow ()