import time
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class Scraper(object):

    def __init__(self, url, title = None):
        self.url = url
        self.title = title
        self.get_first_chapter()

    def get_first_chapter(self):
        if self.url.startswith('https://www.fanfiction.net/s/'):
            chap_pos = self.url.find('.net/s/') + len('.net/s/') + 1
            chap_end = self.url.find('/', chap_pos)

            if chap_end > 0:
                self.url = self.url[0:chap_end]


    def scrape(self):
        """
        Run scraper on FF Website.

        """
        pwd = os.getcwd()

        # Tell ChromeDriver to be headless, so it doesn't open up a browser.
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('log-level=3')

        browser = webdriver.Chrome(chrome_options=options)

        print('getting first chapter in story from url: ', self.url)
        browser.get(self.url)
        info = self.get_story_info(browser)
        title = info['title'] if self.title is None else self.title

        if not os.path.exists(os.path.join(pwd,title)):
            os.mkdir(os.path.join(pwd, title))

        if not os.path.exists(os.path.join(pwd,title, 'chapters')):
            os.mkdir(os.path.join(pwd, title, 'chapters'))


        done = False
        with open(os.path.join(pwd,title,'full_story.html'), 'w+', encoding='utf-8') as file:
            i = 1
            self.write_story_to_file(pwd, title, i, browser, file)
            done = self.go_to_next_page_if_exists(browser, i)
            
            while not done:    
                i+=1

                print("[%s] Got next page in story. Chapter number is %i" % (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), i))

                self.write_story_to_file(pwd, title, i, browser, file)

                done = self.go_to_next_page_if_exists(browser, i)

        return os.path.join(pwd, title), i, info

    def go_to_next_page_if_exists(self, browser, i):
        try:
            element = browser.find_element_by_xpath('//button[text()="Next >"]')

            print('Going to next chapter at location ' + element.get_attribute('onClick'))

            element.click()
            return False
        except Exception:
            print(("[%s] Done finding all pages! Found %d Chapters!" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), i)))
            
        return True

    def write_story_to_file(self, pwd, title, i, browser, full_story_file):
        with open(os.path.join(pwd, title, 'chapters', 'chapter_' + str(i)) + '.html', 'w', encoding='utf-8') as file:
            element = self.get_story_text_browser_element(browser)                

            print("[%s] Results loaded." % (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            file.write(element)

        full_story_file.write("\n" + element + "\n")
        

    def get_story_text_browser_element(self, browser):
        element = None
        while not element:
            try:
                element = browser.find_element_by_id('storytext')
            except Exception as e:
                print('Refreshing page and retrying due to error {}.'.format(str(e)))
                browser.refresh()
        return element.get_attribute('innerHTML')

    def get_story_info(self, element):
        try:
            element = element.find_element_by_id('profile_top')

            info = {}

            print("Getting story title")
            name = element.find_element_by_tag_name('b')
            info['title'] = name.text

            print('Getting Author Information')
            self.get_author_info(element, info)                    
            
            print('Getting story description')
            self.get_story_description(element, info)
            
            print('Getting story metadata')
            span_elems = element.find_elements_by_tag_name('span')
            metadata = span_elems[3].text

            print('Getting last story update date')
            date_updated = span_elems[5].text

            info['date'] = date_updated

            print(info)

            return info                   

        except Exception as e:
            print('Error parsing story info! Error was:', e)
            raise e

    def get_story_description(self, element, info):
        div_elems = element.find_elements_by_tag_name('div')
        info['description'] = div_elems[1].text

    def get_author_info(self, element, info):
        a_elems = element.find_elements_by_tag_name('a')
        user_link = 'https://www.fanfiction.net/u/'

        for elem in a_elems:
            href = elem.get_attribute('href')
            if href.startswith(user_link):
                print(href)

                author_info = href[len(user_link):].split('/')

                author_name = author_info[1]
                author_id = author_info[0]
                print(author_id, author_name, author_info)

                info['author_info'] = {'name':author_name, 'id':author_id}
                break
