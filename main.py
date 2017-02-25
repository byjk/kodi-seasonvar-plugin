#!/usr/bin/python
# -*- coding: utf-8 -*-

from seasonvar_grabber import *

import urllib
import sys
import json
import os

import xbmcgui
import xbmcplugin
import xbmcaddon


__addon__ = xbmcaddon.Addon()
__profile__ = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__last__ = os.path.join(__profile__,'last.log')
__action__ = '-'

def add_dir(url, name, iconImage, mode):
    u = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&mode=" + str(mode) +
         "&name=" + urllib.quote_plus(name))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=iconImage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                     url=u, listitem=liz, isFolder=True)
    return ok


def get_keyboard(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return unicode(keyboard.getText(), "utf-8")
    return default


def index(page, name):
    html = SeasonvarWebOpener().get_html(page)
    m = re.findall('var\s+id\s*=\s*\"(\d+)\"', html)
    if m:
        id = m[0]
        serial_id = re.findall('var\s+serial_id\s*=\s*\"(\d+)\"', html)[0]
        secure = re.findall('var\s+secureMark\s*=\s*\"(.*)\"', html)[0]
        print_playlist(id, secure, name)
    else:
        m = re.findall('php\?help_id=2', html)
        if m:
            xbmcgui.Dialog().ok('Ошибка','По просьбе правообладателя, сезон заблокирован для вашей страны. ')
        else:
            xbmcgui.Dialog().ok('Ошибка','Что-то пошло не так')


def get_file_links(json_response):
    files = []
    for row in json_response['playlist']:
        if row.has_key('file'):
            files.append(row['file'])
        elif row.has_key('playlist'):
            for row2 in row['playlist']:
                files.append(row2['file'])
    return files


def print_playlist(id, secure, name):
    url = 'http://seasonvar.ru/playls2/' + secure + 'x/trans/' + id + '/list.xml'
    json_response = SeasonvarWebOpener().get_json(url)
    files = get_file_links(json_response)
    i = 0
    for one_file in files:
        i = i + 1
        add_downLink(name + " " + str(i), one_file, 2)


def add_downLink(name, url, mode):
    u = (sys.argv[0] +
         "?url=" + urllib.quote_plus(url) +
         "&mode=" + str(mode) +
         "&name=" + urllib.quote_plus(name))
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="icon.png",path=u)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'True')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                     url=u, listitem=liz, isFolder=False)
    return ok


def play(handle, url, name):
    play_item = xbmcgui.ListItem(label=name,path=url)
    play_item.setInfo('video', {'Title': name})
    xbmcplugin.setResolvedUrl(handle, True, listitem=play_item)


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


def search(localpath, handle, url):
    if url:
        show_search_list(localpath, handle, url)
        return
    q = get_keyboard(heading='Введите название сериала')
    q = q.encode('utf-8')
    if q:
        title = urllib.quote_plus(q)
        searchUrl = 'http://seasonvar.ru/autocomplete.php?query=' + title
        if show_search_list(localpath, handle, searchUrl) > 0:
            with open(__last__, 'a') as f:
                f.write(q+"\n")
    # else:
    #     xbmc.log("action!")
    #     # xbmc.executebuiltin('Action(ParentDir)')
    #     global __action__ 
    #     __action__ = 'Action(Back)'
        

def show_search_list(localpath, handle, searchUrl):
    data = SeasonvarWebOpener().get_html(searchUrl)
    # xbmc.log(data)
    data = json.loads(data)
    serials = []
    if 'query' in data and 'id' in data and 'suggestions' in data:
        total = len(data["suggestions"])
        for x in range(0, total):
            serials.append(Serial(
                "http://seasonvar.ru/" + data["data"][x],
                data["id"][x] if len(data["id"]) > x else "",
                data["suggestions"][x].encode('utf8')))
        for serial in serials:
            add_dir(serial.get_url(), serial.get_name(), serial.get_thumb(), 1)
    return len(serials)


def main():
    if not os.path.exists(__profile__):
        os.makedirs(__profile__)

    params = get_params()
    url = None
    name = None
    mode = None
    global __action__ 

    try:
        url = urllib.unquote_plus(params["url"])
    except:
        pass
    try:
        name = urllib.unquote_plus(params["name"])
    except:
        pass
    try:
        mode = int(params["mode"])
    except:
        pass

    localpath = sys.argv[0]
    handle = int(sys.argv[1])
    
    # xbmc.log("localpath: "+localpath+" url:"+str(url)+" name:"+str(name)+" mode:"+str(mode))

    grabber = SeasonvarGrabber()

    if mode == 4:
        os.remove(__last__)
        __action__ = "Container.Refresh"
        
       
    # first page
    if mode is None:
        li = xbmcgui.ListItem("Поиск")
        u = localpath + "?mode=3"
        xbmcplugin.addDirectoryItem(handle, u, li, True)
        if os.path.isfile(__last__):
            with open(__last__) as f:
                q = f.readlines()
                for s in q:
                    if s != "":
                        li = xbmcgui.ListItem(s)
                        title = urllib.quote_plus(s)
                        searchUrl = 'http://seasonvar.ru/autocomplete.php?query=' + title
                        u = localpath + "?mode=3&url="+urllib.quote_plus(searchUrl)
                        xbmcplugin.addDirectoryItem(handle, u, li, True)
                if len(q) > 0:
                    li = xbmcgui.ListItem("Очистить историю поиска")
                    xbmcplugin.addDirectoryItem(handle, localpath+"?mode=4", li, False)
        # for serial in grabber.get_main_page_data():
        #     add_dir(serial.get_url(), serial.get_name(), serial.get_thumb(), 1)

    # page with links
    elif mode is 1:
        index(url, name)

    elif mode is 2:
        play(handle, url, name)

    elif mode == 3:
        search(localpath, handle, url)

    if handle != -1:
        xbmcplugin.endOfDirectory(handle)
    
    if __action__ != '-':
        # xbmc.log("action: "+__action__)
        xbmc.executebuiltin(__action__)        
main()
