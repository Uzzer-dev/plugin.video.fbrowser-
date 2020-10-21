# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, utils, run
from codequick.utils import urljoin_partial, bold
from codequick.script import Settings
import urlquick
import xbmcgui
import json
import uuid
import re
import xbmcplugin
from defusedxml.ElementTree import fromstring
from defusedxml.ElementTree import ParseError


# noinspection PyUnusedLocal
@Route.register
def root(plugin, content_type="video"):
    
    item = Listitem()
    item.label= "nserv.host [supported]"
    item.set_callback(open_page, url="/", base_url="http://nserv.host:5300")
    yield item

    item = Listitem()
    item.label= "filmix.red [partically supported]"
    item.set_callback(open_page, url="/", base_url="http://filmix.red")
    yield item

    item = Listitem()
    item.label= "spiderxml search [partically supported][untested]"
    item.set_callback(do_input_page, url="/search", base_url="http://spiderxml.com")
    yield item
    
    item = Listitem()
    item.label= "cooltv.info [supported][untested]"
    item.set_callback(open_page, url="/start", base_url="http://cltv.club")
    yield item



@Route.register
def open_page(plugin, url, params={"box_mac" : ':'.join(re.findall('..', '%012x' % uuid.getnode())), "box_user" : Settings.get_string("email")}, search_query=None, base_url=None):
    items_m3u = None
    items_et = None
    if search_query:
        params.update({"search" : search_query})
    else:
        params.update({"search" : None})
    if Settings.get_string("mac") != "default":
        params.update({"box_mac" : Settings.get_string("mac")})
    url_constructor = urljoin_partial(base_url)
    resp = urlquick.get(url_constructor(url), params=params, max_age=1, headers={"Accept":"text/xml"}).text
    try:
        items = json.loads(resp)
    except (ValueError, RuntimeError) as identifier:
        items = dict({'channels':[]})
        items_et = fromstring(resp.encode("utf-8"))
        


    if items_m3u is not None:
        pattern = re.compile('(#EXTGRP.+)|(#EXTM3U.+)|(#EXTINF:-1 ,)|(#EXTINF:)')
        cleaned_data = re.sub(pattern, '', resp)
        pattern = re.compile('.+')
        result = re.findall(pattern, cleaned_data)
        for item in range(0, len(result) - 1, 2):
            list_item = Listitem()
            list_item.label = result[item]
            list_item.set_path(result[item + 1], is_folder=False, is_playable=True)
            yield list_item
            continue

    elif items_et is not None:
        for item in list(items_et.iterfind("channel")):
            i = Listitem()
            if item.find('title') is not None:
                i.label = item.find('title').text
            if item.find('description') is not None:
                i.info.plot = remove_html_tags(item.find('description').text)
            if item.find('logo_30x30') is not None:
                i.art.thumb = remove_html_tags(item.find('logo_30x30').text)
            if item.find('search_on') is not None:
                i.set_callback(do_input_page, url=item.find('playlist_url').text, base_url=base_url)
            elif item.find('playlist_url') is not None:
                i.set_callback(open_page, url=item.find('playlist_url').text, base_url=base_url)
            elif item.find('stream_url') is not None:
                i.set_path(item.find('stream_url').text, is_folder=False, is_playable=True)
            yield i

    
    else:
        for i in items['channels']:
            item = Listitem()
            if 'details' in i and isinstance(i['details'], dict):
                if 'poster' in i['details']:
                    item.art.poster = i['details']['poster']
                if 'released' in i['details']:
                    item.info.premiered = i['details']['released']

            if 'background-image' in items:
                item.art.landscape = items['background-image']
            item.label = remove_html_tags(i['title'])
            if 'logo_30x30' in i:
                item.art.thumb = i['logo_30x30']
            if 'description' in i:
                item.info.plot = remove_html_tags(i['description'])
            if 'search_on' in i:
                print("search method user")
                item.set_callback(do_input_page, url=i['playlist_url'], base_url=base_url)
            elif 'playlist_url' in i:
                print("dir method user")
                item.set_callback(open_page ,url=i['playlist_url'], base_url=base_url)
            elif 'stream_url' in i:
                print("stream method user")
                item.set_path(i['stream_url'], is_folder=False, is_playable=True)
            yield item
    
def remove_html_tags(text):
    """Remove html tags from a string"""
    if text is not None:
        clean = re.compile('(<style>(.+?)<\/style>)|(<.*?>)')
        return re.sub(clean, ' ', text.replace('\n', ''))
    else:
        return ""
    
@Route.register
def do_input_page(plugin, url, base_url):
    input_query = utils.keyboard("Input data:")
    return open_page(plugin, url, search_query=input_query, base_url=base_url)