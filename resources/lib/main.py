# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, utils, run, Script
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
import sys

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
def open_page(plugin, url, params={"box_mac" : ''.join(re.findall('..', '%012x' % uuid.getnode())), "box_user" : Settings.get_string("email")}, search_query=None, base_url=None):
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
    
    if '<?xml version="1.0"' in resp:
        return open_xml_page(page=resp, base_url=base_url)
    elif '"title":' in resp:
        return open_json_page(plugin, page=resp, base_url=base_url)
    elif '#EXTINF:' in resp:
        return open_m3u_playlist(playlist=resp, base_url=base_url)
        



@Route.register
def open_m3u_playlist(playlist, base_url):
    pattern = re.compile('(#EXT.+\,)|(#EXT.+)')
    cleaned_data = re.sub(pattern, '', playlist)
    pattern = re.compile('.+')
    result = re.findall(pattern, cleaned_data)
    for item in range(0, len(result) - 1, 2):
        list_item = Listitem()
        if 'youtube.com' or 'youtu.be' in result['item']:
            list_item.set_callback(play_youtubedl_url, url=result[item + 1])
        else:
            list_item.set_path(path=result[item + 1])
        list_item.label = result[item]
        yield list_item
        
        
@Route.register
def open_xml_page(page, base_url):
    items = dict({'channels':[]})
    items_et = fromstring(page.encode("utf-8"))
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
            if 'youtube.com' or 'youtu.be' in item.find('stream_url').text:
                i.set_callback(play_youtubedl_url, url=item.find('stream_url').text)
            else:
                i.set_path(item.find('stream_url').text, is_folder=False, is_playable=True)
        yield i

@Route.register 
def open_json_page(plugin, page, base_url):
    items = json.loads(page)
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
            if 'youtube.com' or 'youtu.be' in i['stream_url']:
                item.set_callback(play_youtubedl_url, url=i['stream_url'])
            else:
                item.set_path(path=i['stream_url'])
        yield item

@Resolver.register
def play_youtubedl_url(plugin, url):
    try:
        return plugin.extract_source(url)
    except RuntimeError:
        Script.notify("Unable to open stream", "Try another one", icon=Script.NOTIFY_ERROR)

def remove_html_tags(text):
    """Remove html tags from a string"""
    if text is not None:
        clean = re.compile('(<style.+\>(.+?)<\/style>)|(<.*?>)')
        return re.sub(clean, ' ', text.replace('\n', ''))
    else:
        return ""
    
@Route.register
def do_input_page(plugin, url, base_url):
    input_query = utils.keyboard("Input data:")
    return open_page(plugin, url, search_query=input_query, base_url=base_url)
