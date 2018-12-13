import sys
import os
from os import path

from datetime import datetime
import argparse, uuid
from epub_converter_lib.epub_converter import ConvertTextToEPub
from Scraper import Scraper

def update_story_info(args, story_info):
    args.title = story_info['title']
    args.description = story_info['description']
    print(story_info['description'])
    args.author = story_info['author_info']['name']

if __name__ == '__main__':

    sys.path.append(path.dirname(path.dirname(__file__)))
 
    parser = argparse.ArgumentParser(description='convert text files to epub document.')
    parser.add_argument('destination', type=str,
                        help='the name of the epub document')
    parser.add_argument('--sources', nargs='+',
                        help='the text files to include in the epub', dest='sources')
    parser.add_argument('--url', dest='url')
    parser.add_argument('--ff_net_id', '-fid', dest='ff_net_id')
    parser.add_argument('--images', nargs='+', help='images to include in the epub')
    parser.add_argument('--keep-line-breaks', action='store_true')
    parser.add_argument('--nokeep-line-breaks', action='store_false', dest='keep_line_breaks')
    parser.add_argument('--type')
    parser.add_argument('--title')
    parser.add_argument('--author')
    parser.add_argument('--creator')
    parser.add_argument('--description')
    parser.add_argument('--publisher')
    parser.add_argument('--date', default=datetime.date(datetime.today()))
    parser.add_argument('--language')
    parser.add_argument('--identifier', default=str(uuid.uuid4()).replace('-', ''))

    args = parser.parse_args()

    args.keep_line_breaks = True
    
    url = args.url

    if 'ff_net_id' in args and args.ff_net_id:
        url = 'https://www.fanfiction.net/s/' + args.ff_net_id
    
    scraper = Scraper(url, args.title)
    loc, num_chapters, story_info = scraper.scrape()
    chapter_loc = os.path.join(loc, 'chapters')

    sources = [
        {
            "path": os.path.join(chapter_loc, 'chapter_' + str(i) + '.html'),
            'name': 'chapter_' + str(i),
            'type': 'html',
            'fileName': 'chapter_' + str(i) + '.html'
        } for i in range(1, num_chapters + 1) 
    ]
    
    update_story_info(args, story_info)
    print('using title', args.title)

    ConvertTextToEPub().convert_text_to_epub(args.destination, sources,story_info)

"python ArgsParser.py epub.epub --ff_net_id 11759933"