import os
import csv
import time
import random
import config
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
        
        # User to follow or unfollow
        self.profile_links = []
        
        # History file
        self.history_file = os.path.join (os.path.dirname (__file__), "history.csv")
        
        # Css selectors
        self.selectors = {
            "post": "._ac7v._al3n ._aabd._aa8k._al3l a",
            "show_post_likes": "span.x1lliihq > a",
            "users_posts_likes": "span.x1lliihq.x193iq5w.x6ikm8r a",
            "users_posts_likes_wrapper": '[role="dialog"] [style^="height: 356px;"]',
            "users_posts_likes_load_more": "",
            "users_posts_comments": "ul._a9ym .xt0psk2 > a",
            "users_posts_comments_wrapper": ".x10l6tqk.xexx8yu.x1pi30zi > .x5yr21d > ul._a9z6._a9za",
            "users_posts_comments_load_more": ".x10l6tqk.xexx8yu.x1pi30zi > .x5yr21d > ul._a9z6._a9za > li button",
        }
    
        # Start chrome
        super ().__init__ (headless=self.headless, chrome_folder=self.chrome_folder, start_killing=True)
        
        # Get history rows
        self.followed_classic, self.followed_advanced, \
        self.unfollowed, self.history = self.__get_history__ ()
        
    def __get_history__ (self) -> tuple:
        """ Read rows from history file

        Returns:
            tuple: lists of followed and unfollowed users
                list: followed_classic
                list: followed_advanced
                list: unfollowed
                list: history_rows
        """
        
        with open (self.history_file, "r") as file:
            csv_reader = csv.reader (file)
            history = list (csv_reader)
            
        followed_classic = list(map(lambda row: row[0], filter(lambda row: row[1] == "followed_classic", history)))
        followed_advanced = list(map(lambda row: row[0], filter(lambda row: row[1] == "followed_advanced", history)))
        unfollowed = list(map(lambda row: row[0], filter(lambda row: row[1] == "unfollowed", history)))
        history_rows = list(map(lambda row: row[0], history))
        
        return followed_classic, followed_advanced, unfollowed, history_rows      
    
    def __wait__ (self, message:str=""):
        """ Wait time and show message

        Args:
            message (str, optional): message to show after wait time. Defaults to "".
        """
        
        time.sleep (random.randint(30, 180))
        if message:
            print (message)
    
    def __load_links__ (self, selector_link:str, selector_wrapper:str, load_more_selector:str=""): 
        """ get links from scrollable element

        Args:
            selector_link (str): css selector of the link
            selector_wrapper (str): css selector of the scroll element
            load_more_selector (str, optional): Selector of button for load more links. Defaults to "".
        """
                
        scroll_by = 2000
                
        # Gennerate list of users to skip
        skip_users = []
        skip_users += self.followed_advanced
        skip_users += self.followed_classic
        skip_users += self.unfollowed
        
        more_links = True
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
                if link not in skip_users and link not in self.profile_links: 
                    self.profile_links.append(link)
                    
                # Count number of links
                links_num = len (self.profile_links)
                if links_num >= self.max_follow: 
                    more_links = False
                    break
            
            # Go down
            elems = self.scraper.get_elems (selector_wrapper)
            if elems:
                self.scraper.driver.execute_script(f"arguments[0].scrollBy (0, {scroll_by});", elems[0])
            
            # Click button for load more results
            if load_more_selector:
                elems = self.get_elems (load_more_selector)
                if elems:
                    self.click_js (load_more_selector)
                    time.sleep(3)
    
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
        
    def __follow_like_users__ (self, max_posts:int=3, follow_type:str=""):
        """ Follow and like posts of users from a profile_links

        Args:
            max_posts (int, optional): number of post to like. Defaults to 3.
            follow_type (str, optional): type of follow. Defaults to "".
        """
        
        for user in self.profile_links:
            
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
            
            # Save current user in history
            self.__save_user_history__ (user, follow_type)
            
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
    
    def __get_users__ (self):
        """ Return users to follow from likes, comments and followers
        """
        
        # Loop each target user
        for user in self.list_follow: 
            
             # Show followers page 
            url = f"https://www.instagram.com/{user}"
            self.__set_page_wait__ (url)
            
            # Get posts links
            posts_links = self.get_attribs (self.selectors["post"], "href")
            
            # Open each post details
            for post_link in posts_links:
                
                self.__set_page_wait__ (post_link)
                
                # Open post likes
                self.click_js (self.selectors["show_post_likes"])
                self.refresh_selenium ()
                
                # Go down and get profiles links from likes
                self.__load_links__ (
                    self.selectors["users_posts_likes"], 
                    self.selectors["users_posts_likes_wrapper"], 
                    self.selectors["users_posts_likes_load_more"],                     
                )
                
                # Open post comments
                self.__set_page_wait__ (post_link)
                
                # Go down and get profiles links from comments
                self.__load_links__ (
                    self.selectors["users_posts_comments"], 
                    self.selectors["users_posts_comments_wrapper"], 
                    self.selectors["users_posts_comments_load_more"], 
                )
                
                # End loop if max users reached
                if len(self.profile_links) >= self.max_follow:
                    break

    def follow_classic (self):
        """ Follow users from current followers list of an specific users
        """
        
        # Loop each user
        for user in self.list_follow:
                        
            print (f"getting users from followers list {user}...")
            
            # Show followers page 
            url = f"https://www.instagram.com/{user}/followers/"
            self.set_page (url)
                    
            # Go down and get profiles links
            self.__load_links__ (
                self.selectors["followers_links"], 
                filter_classic=True,
                filter_unfollowed=True,
                load_from="followers"
            )
            
        print (f"{len(self.profile_links)} users found")
        
        # Follow users
        self.__follow_like_users__ (follow_type="followed_classic")
    
    def follow_advanced (self):
        """ Follow users from linkes of last posts from specific users
        """
        
        # Loop each user
        for user in self.list_follow:
            
            # Show followers page 
            url = f"https://twitter.com/{user}"
            self.__set_page_wait__ (url)
            
            # Get posts links
            posts_links = self.get_attribs (self.selectors["post_link"], "href")
            
            # Open each post details
            for post_link in posts_links:
                
                # Open post likes
                post_link_likes = post_link + "/likes"
                self.__set_page_wait__ (post_link_likes)
                
                # Go down and get profiles links from likes
                self.__load_links__ (
                    self.selectors["post_like_user"], 
                    filter_advanced=True,
                    filter_unfollowed=True,
                    load_from="likes"
                )
                
                # Open post comments
                self.__set_page_wait__ (post_link)
                
                # Go down and get profiles links from comments
                self.__load_links__ (
                    self.selectors["post_like_user"], 
                    filter_advanced=True,
                    filter_unfollowed=True,
                    load_from="comments"
                )
                
                # End loop if max users reached
                if len(self.profile_links) >= self.max_follow:
                    break
                
        print (f"{len(self.profile_links)} users found")
                
        # Follow users
        self.__follow_like_users__ (follow_type="followed_advanced")
    
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
            
            
    