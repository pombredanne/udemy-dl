#!/usr/bin/env python
# -*- coding: utf8 -*-

import requests
import argparse
import getpass
import sys
import re
import os
import time
import urllib

class Session:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0',
               'X-Requested-With': 'XMLHttpRequest',
               'Referer': '	http://www.udemy.com/'}

    def __init__(self):
        self.session = requests.Session()

    def get(self, url):
        return self.session.get(url, headers = self.headers)

    def post(self, url, data):
        return self.session.post(url, data, headers = self.headers)


session = Session()

def login(username, password):
    login_url = 'http://www.udemy.com/login/login-submit' # Yes, no SSL
    payload = {'isSubmitted': 1, 'email': username, 'password': password, 'displayType': 'json'}
    response = session.post(login_url, payload).json()
    if response.has_key('error'):
        print(response['error']['message'])
        sys.exit(1)

def get_course_id(course_link):
    response = session.get(course_link)
    matches = re.search('data-courseId="(\d+)"', response.text)
    return matches.groups()[0]

def get_video_links(course_id):
    course_data = session.get('http://www.udemy.com/api-1.0/courses/%s/curriculum?closeSessionWrites=1'%(course_id)).json()

    chapter = None
    video_list = []

    lecture_number = 0
    chapter_number = 0
    # A udemy course has chapters, each having one or more lectures
    for item in course_data:
        if item['__class'] == 'chapter':
            chapter = item['title']
            chapter_number += 1
            lecture_number = 1
        elif item['__class'] == 'lecture' and item['asset_type'] == 'Video':
            lecture = item['title']
            try:
                video_url = item['asset']['download_url']['video'][0]
                video_list.append({'chapter': chapter, 
                                   'lecture': lecture, 
                                   'video_url': video_url,
                                   'lecture_number': lecture_number, 
                                   'chapter_number': chapter_number})
            except KeyError:
                print 'Cannot download lecture "%s" because it is not downloadable' %(lecture)
            lecture_number += 1
    return video_list

def mkdir(directory) :
    if not os.path.exists(directory):
        os.makedirs(directory)

def dl_progress(num_blocks, block_size, total_size):
    progress = num_blocks * block_size * 100 / total_size
    if num_blocks != 0:
        sys.stdout.write(4 * '\b')
    sys.stdout.write('%3d%%' % (progress))

def get_video(directory, filename, link):
    print('Downloading %s  ' %(filename)),
    mkdir(directory)
    os.chdir(directory)
    if not os.path.exists(filename):
        urllib.urlretrieve(link, filename, reporthook = dl_progress)
    os.chdir('..')
    print

def udemy_dl(username, password, course_link):
    login(username, password)

    course_id = get_course_id(course_link)

    for video in get_video_links(course_id):
        directory = '%02d %s'%(video['chapter_number'], video['chapter'])
        filename = '%03d %s.mp4'%(video['lecture_number'], video['lecture'])
        filename = filename.replace('/', '|') # Sanitize file name

        get_video(directory, filename, video['video_url'])


    session.get('http://www.udemy.com/user/logout')

def main():
    parser = argparse.ArgumentParser(description='Fetch all the videos for a udemy course')
    parser.add_argument('link', help='Link for udemy course', action='store')
    parser.add_argument('-u', '--username', help='Username/Email', default=None, action='store')
    parser.add_argument('-p', '--password', help='Password', default=None, action='store')

    args = vars(parser.parse_args())

    username = args['username']
    password = args['password']
    link = args['link']

    if not username:
        print('Username/Email:'),
        username = raw_input()
    if not password:
        password = getpass.getpass(prompt='Password: ')

    udemy_dl(username, password, link)

if __name__ == '__main__':
    main()
