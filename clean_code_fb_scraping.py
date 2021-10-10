import itertools
import argparse
import time
import json
import csv
import os
import re

from tqdm import tqdm
from selenium import webdriver
from pymongo import MongoClient
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.options import Options


def _start_browser(webdriverPath:str= None):
  """Define the webdriver options and start it"""

  # chromedriver should be in the same folder as file
  option = Options()
  option.add_argument("--disable-infobars")
  option.add_argument("start-maximized")
  option.add_argument("--disable-extensions")
  # Making Notifications off automatically
  prefs = {"profile.default_content_setting_values.notifications" : 2}
  option.add_experimental_option("prefs",prefs)
  browser = webdriver.Chrome(executable_path=webdriverPath, options=option)
  print("[INFO]: Webdriver was started Successfully")
  return browser

def _get_facebook_credentials(fbCredsPath:str= None):
  """Get the email and password from the credentials text file"""
  with open(fbCredsPath) as file:
      email = file.readline().split('"')[1]
      password = file.readline().split('"')[1]
  print("[EMAIL]: {}".format(email))
  print("[PASSWORD]: {}".format(password))
  return email, password

def _login(browser, fbCredsPath:str= None):
    """Login to facebook web site and suspends execution for 5 seconds"""
    email, password = _get_facebook_credentials(fbCredsPath)
    browser.get("http://facebook.com")
    # maximize the window 
    browser.maximize_window()
    # accept the cookies
    cookies = browser.find_element_by_xpath('/html/body/div[3]/div[2]/div/div/div/div/div[3]/button[2]')
    cookies.click()    
    # send the email and password to the authentification items
    browser.find_element_by_name("email").send_keys(email)
    browser.find_element_by_name("pass").send_keys(password)
    # press the button login 
    browser.find_element_by_css_selector("button[name='login']").click()
    print("[INFO]: login Successfully...")
    time.sleep(5)

def _search_topic(browser, topic:str= None):
    """Make research to find posts that match the requested topic"""
    browser.get("https://www.facebook.com/search/posts/?q=" + topic)
    time.sleep(5)

def _count_needed_scrolls(browser, infiniteScroll= False, numOfPost= 24):
    """Count the needed scrolls to reach the requested numOfPost with a gap of 8"""
    if infiniteScroll:
        lenOfPage = browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;"
        )
    else:
        # gap of 8 post per scroll 
        lenOfPage = int(numOfPost / 8)
  
    print('[INFO]: Number needed scroll '.format(str(lenOfPage)))
    return lenOfPage
  
def _scroll(browser, lenOfPage, infiniteScroll= False):
    """Scroll all along the height of the content of the page either if it is
    an infinite scroll or a finite scroll so that it displays the whole source
    that we want to capture.
    """
    
    EndOfPage = False
    lastScroll = -1
    
    # looping through the paged pages
    while not EndOfPage:
        
        print("[INFO]: scrolling down to get the full page...")
        if infiniteScroll:
            lastScroll = lenOfPage
        else:
            lastScroll += 1


        if infiniteScroll:
            # scrolls the document until the end of the page
            lenOfPage = browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                "lenOfPage;")
        else:
            # scrolls the document all a long the height of the content
            browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return "
                "lenOfPage;")
            
        # wait for the browser to load
        time.sleep(5)
        
        # stop scrolling if atteimpt the end of page
        if lastScroll == lenOfPage:
            EndOfPage = True
    
def _extract_page_name(item):
    """Get the name of the used who posted the publication"""
    text = item.text.split('\xa0 · \xa0 ·')[0].split('Page')[0]
    return text

def _extract_post_date(item):
    """Get the date when the publication was posted"""
    text = item.text.split('\xa0 · \xa0 ·')[0][-13:].replace('.','')
    cutDate = [''.join(x) for _, x in itertools.groupby(text, key=str.isdigit)]
    if cutDate[0].isdigit():
        return text
    else:
        return ''.join([elm for elm in cutDate[-2:]])
    
def _extract_post_content(item):
    """Get the textual content of the publication"""
    text = item.text.split("\xa0 · \xa0 ·")[1]
    return text

def _extract_post_link(item):
    """Get the link to the publication"""
    link = ""
    post_link_elm = item.find_all("a")
    for a_elm in post_link_elm:
        link = a_elm.attrs["href"]
    return link

def _extract_post_images(item):
    """Extract all images inclosed to the publication"""
    images = list()
    post_img_elm = item.findAll('img')
    for img_elm in post_img_elm:
        images.append(img_elm['src'])
    r = re.compile("^https://scontent")
    images = list(filter(r.match, images))
    return images

def _grab_page_code(browser):
    """Grab the full page HTML source code"""
    source_data = browser.page_source
    # Parsing the the source code sunig BeautifulSoup
    bs_data = bs(source_data, 'html.parser')
    return bs_data

def _extract_html(bs_data):
    """Open the source code file and pase it using BeautifulSoup"""
    # open the source HTML code of the full content
    with open('./bs.html',"w", encoding="utf-8") as file:
        file.write(str(bs_data.prettify()))

    itemList = bs_data.findAll("div", attrs={'role':"article"}) #"_5pcr userContentWrapper")
    
    allPosts = list()

    for item in tqdm(itemList):
        post = dict()
        post['Name'] = _extract_page_name(item)
        post['Date'] = _extract_post_date(item)
        post['Content'] = _extract_post_content(item)
        post['Link'] = _extract_post_link(item)
        post['Images'] = _extract_post_images(item)
        #[TODO]: Scraping collapsed comments

        #Add to check
        allPosts.append(post)
        with open('./allPosts.json','w', encoding='utf-8') as file:
            file.write(json.dumps(allPosts, ensure_ascii=False).encode('utf-8').decode())

    return allPosts
    
def _store_data_in_mongodb(dbname:str=None):
    client = MongoClient()
    print('[INFO]: {}'.format(client))
    # database
    db = client[dbname]
    # collection
    posts= db["posts"]
    # insert all scraped posts into the created collection
    posts.insert_many(allPosts)
    print('[INFO]: data saved successfully')
    # get the stored usernames of the extracted posts
    print(db.posts.distinct("Name"))
	
	

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Scraping Facebook Page")
    required_parser = parser.add_argument_group("required arguments")
    required_parser.add_argument('-wdpath', '-w', help="The webdriver pathe", required=True)
    required_parser.add_argument('-credspath', '-c', help="The facebook Credentials path", required=True)
    required_parser.add_argument('-topic', '-t', help="The requested topic you wanna scrape", required=True)
    required_parser.add_argument('-dbname', '-d', help="The name of the database", required=True)

    optional_parser = parser.add_argument_group("optional arguments")
    optional_parser.add_argument('-numOfPost', '-n', help="The requested number of post to scrape", type=int)
    optional_parser.add_argument('-infinite', '-i',
                                 help="Scroll until the end of the page (1 = infinite) (Default is 0)", type=int)
    
    args = parser.parse_args()

    browser = _start_browser(args.wdpath)

    _login(browser, args.credspath)

    _search_topic(browser, args.topic)
    getMorePosts = browser.find_element_by_xpath('/html/body/div[1]/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div/div[3]/div/div/div/div/div/div/div[2]/a')
    getMorePosts.click()
    print("[INFO]: Getting more results...")
    

    infinite = False
    if args.infinite == 1:
        infinite = True
    
    numOfPost = 24
    if args.numOfPost:
        numOfPost = args.numOfPost
    
    # scroll down     
    lenOfPage = _count_needed_scrolls(browser, infinite, numOfPost)

    _scroll(browser, lenOfPage, infinite)

    bs_data = _grab_page_code(browser)

    allPosts = _extract_html(bs_data)

    print(allPosts)
    
    _store_data_in_mongodb(args.dbname)
    
    browser.close()


