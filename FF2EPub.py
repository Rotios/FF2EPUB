import sys
import os
from os import path
from datetime import datetime

from epub_converter_lib.epub_converter import ConvertTextToEPub
from Scraper import Scraper
import boto3
import stat

s3 = boto3.client('s3')

def lambda_handler(event, context):

    if 'url' in event:
        url = event['url']
    elif 'ff_net_id' in event:
        url = 'https://www.fanfiction.net/s/' + event['ff_net_id']
    else:
        return "You must pass a url or FF.net story id"
    
    title = None

    if 'title' in event:
        title = event['title']
    dest_dir = "/tmp/" + str(context.aws_request_id) + "/"
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)

    scraper = Scraper(url, dest_dir, title)
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
    
    print('using title', story_info['title'])
    title_key = story_info['title'].replace(" ", "-")
    file_loc =os.path.join(dest_dir, title_key + '.epub')
    
    ConvertTextToEPub().convert_text_to_epub(file_loc, sources, story_info)

    story_id = url.split("/s/")[1].split('/')[0]
    
    final_dest = story_id + "/" + title_key + ".epub"
    s3.upload_file(file_loc, os.environ['S3_UPLOAD_BUCKET'], final_dest)

    return final_dest