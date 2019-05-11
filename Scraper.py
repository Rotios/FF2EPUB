import time
import os
from datetime import datetime

from requests_html import HTMLSession

FANFICTION_STORY_BASE_URL = 'https://www.fanfiction.net/s/'
FANFICTION_BASE_URL = 'https://www.fanfiction.net'

class Scraper(object):

    def __init__(self, url, title = None):
        self.url = url
        self.title = title
        self.get_first_chapter()

    def get_first_chapter(self):
        if self.url.startswith(FANFICTION_STORY_BASE_URL):
            chap_pos = self.url.find('.net/s/') + len('.net/s/') + 1
            chap_end = self.url.find('/', chap_pos)

            if chap_end > 0:
                self.url = self.url[0:chap_end]


    def scrape(self):
        """
        Run scraper on FF Website.

        """
        pwd = os.getcwd()

        session = HTMLSession()

        print('getting first chapter in story from url: ', self.url)

        request = session.get(self.url)
        info = self.get_story_info(request)

        title = info['title'] if self.title is None else self.title

        if not os.path.exists(os.path.join(pwd,title)):
            os.mkdir(os.path.join(pwd, title))

        if not os.path.exists(os.path.join(pwd,title, 'chapters')):
            os.mkdir(os.path.join(pwd, title, 'chapters'))

        with open(os.path.join(pwd, title,'full_story.html'), 'w+', encoding='utf-8') as file:
            i = 1
            self.write_story_to_file(pwd, title, i, request, file)
            request = self.go_to_next_page_if_exists(session, request, i)
            
            while request:    
                i+=1

                print("[%s] Got next page in story. Chapter number is %i" % (
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), i))

                self.write_story_to_file(pwd, title, i, request, file)

                request = self.go_to_next_page_if_exists(session, request, i)

        return os.path.join(pwd, title), i, info

    def go_to_next_page_if_exists(self, session, request, i):
        try:
            next = [b for b in request.html.find('button') if 'Next' in b.text]

            if len(next) > 0:
                next = next[0].attrs['onclick']
                if 'self.location=\'' in next:
                    next = next[len('self.location=\''):-1]
                
                print('Going to next chapter at location ' + next)
                
                return session.get(FANFICTION_BASE_URL + next)

        except Exception:
            print(("[%s] Done finding all pages! Found %d Chapters!" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), i)))
            
        return None

    def write_story_to_file(self, pwd, title, i, request, full_story_file):
        with open(os.path.join(pwd, title, 'chapters', 'chapter_' + str(i)) + '.html', 'w', encoding='utf-8') as file:
            element = self.get_story_text_browser_element(request)                

            print("[%s] Results loaded." % (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            file.write(element)

        full_story_file.write("\n" + element + "\n")
        

    def get_story_text_browser_element(self, request):
        element = None
        while not element:
            try:
                element = request.html.find('#storytextp')[0]
            except Exception as e:
                print('Refreshing page and retrying due to error {}.'.format(str(e)))
                raise e
        return element.html

    def get_story_info(self, request):
        try:
            element = request.html.find('#profile_top')[0]

            print("Getting story title")

            info = {}
            sel = 'b.xcontrast_txt'
            name = element.find(sel)[0]
            info['title'] = name.text

            print('Getting Author Information')
            self.get_author_info(element, info)                    
            
            print('Getting story description')
            self.get_story_description(element, info)
            
            print('Getting story metadata')
            span_elems = element.find('span')
            metadata = span_elems[2].text

            print('Getting last story update date')
            date_updated = span_elems[3].text

            info['date'] = date_updated

            print(info)

            return info                   

        except Exception as e:
            print('Error parsing story info! Error was:', e)
            raise e

    def get_story_description(self, element, info):
        div_elems = element.find('div.xcontrast_txt')
        info['description'] = div_elems[0].text

    def get_author_info(self, element, info):
        a_elems = element.absolute_links
        user_link = 'https://www.fanfiction.net/u/'

        link = [a for a in a_elems if user_link in a]

        if len(link) > 0:

            href = link[0]
            
            print(href)

            author_info = href[len(user_link):].split('/')

            author_name = author_info[1]
            author_id = author_info[0]
            print(author_id, author_name, author_info)

            info['author_info'] = {'name':author_name, 'id':author_id}
