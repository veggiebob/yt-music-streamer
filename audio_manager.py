import math
import os, platform
import random
import sys
import time
from threading import Thread
from typing import List, Dict

from pafy.backend_youtube_dl import YtdlPafy
from youtube_dl.utils import ExtractorError

system_name = platform.system().lower()
if system_name == 'windows':
    os.add_dll_directory("C:\Program Files (x86)\VideoLAN\VLC") # this is windows specific, and generally computer specific as well. you need a vlc


import pafy
import vlc


# useful: https://blog.e-zest.com/working-with-python-for-streaming-music-from-youtube
class YTAudio:
    def __init__(self, url=None, initialize=False, vlc_instance=None, player=None):
        # info
        self.title: str = None
        self.yt_video_url: str = url
        self.video: YtdlPafy = None
        self.best_audio_url: str = None
        self.length: int = None  # seconds

        # vlc player stuff
        self.media = None
        self.initialized = False
        self.has_media = False
        self.player:vlc.MediaPlayer = None
        self.has_player = False

        # state control
        self.playing = False
        self.finished = False
        self.paused = False
        self.current_time = 0

        # initialization
        if initialize or vlc_instance is not None or player is not None:
            self.init(vlc_instance=vlc_instance, player=player)

    def init(self, vlc_instance=None, player=None) -> None:
        if self.yt_video_url is None:
            raise Exception("You need to add a url!")
        try:
            self.video = pafy.new(self.yt_video_url)
        except:
            raise Exception("Url '%s' did not work." % self.yt_video_url)
        self.best_audio_url = self.video.getbestaudio().url
        self.length = self.video.length
        self.title = self.video.title
        self.initialized = True

        if vlc_instance is not None:
            self.init_media(vlc_instance)
        if player is not None:
            self.attach_player(player)

    def attach_player(self, player):
        self.player = player
        self.has_player = True

    def init_media(self, vlc_instance):
        if not self.initialized:
            self.init()
        self.media = vlc_instance.media_new(self.best_audio_url)
        self.media.get_mrl()
        self.has_media = True

    def start(self):
        if not self.initialized:
            raise Exception("Needs initialization!")
        if not self.has_media:
            raise Exception("Needs media initialization!")
        if not self.has_player:
            raise Exception("Need to attach a player!")
        if self.playing:
            print('already playing!')
            return
        self.player.set_media(self.media)
        self.player.play()
        self.playing = True
        self.paused = False
        self.finished = False
        self.current_time = 0
        play = Thread(target=self.play_continuous)
        play.start()
        # play.join(timeout=self.length) # because you can pause
        play.join()

    def play_continuous(self) -> None:
        while self.playing:
            self.current_time = self.player.get_time() / 1000
            if self.current_time >= self.length - 2: # for some reason, there is a bit of a discrepancy between length and where it ends
                self.stop()
                break
            while self.paused:
                time.sleep(0.1)

        self.finished = True

    def pause(self):
        self.player.pause()
        self.paused = True

    def resume(self):
        self.player.play()
        self.paused = False

    def stop(self):
        if self.finished:
            return
        self.player.stop()
        self.paused = False
        self.playing = False
        self.finished = True

    def restart (self):
        self.player.set_media(self.media)
        self.player.play()

    def relative_set_per (self, percentage: float):
        self.set_time_per(self.get_time_per() + percentage)

    def relative_set_sec (self, seconds: float):
        self.relative_set_per(seconds/self.length)
        self.player.play()

    def relative_set_min_sec (self, minutes: float, seconds: float):
        self.relative_set_sec(minutes * 60 + seconds)

    def relative_set_hour_min_sec (self, hours: float, minutes: float, seconds: float):
        self.relative_set_min_sec(hours * 60 + minutes, seconds)

    def get_time_per (self) -> float:
        return self.player.get_position()

    def set_time_per (self, percentage: float): # 0 <= percentage <= 1
        if not 0 <= percentage <= 1:
            print('%ss is not a valid time. The video is only %ss long.'%(percentage * self.length, self.length))
            return
        self.player.set_position(percentage)

    def set_time_sec (self, seconds: float):
        per = seconds / self.length
        self.set_time_per(per)

    def set_time_min_sec (self, minutes: float, seconds: float):
        sec = minutes * 60 + seconds
        self.set_time_sec(sec)

    def set_time_hour_min_sec (self, hours: float, minutes: float, seconds: float):
        self.set_time_min_sec(hours * 60 + minutes, seconds)

    def set_volume (self, vol):
        self.player.audio_set_volume(vol)

    def get_time (self) -> str:
        # get the current time as HH:MM:ss
        return YTAudio.sec_to_str(self.current_time)

    def get_length (self) -> str:
        return YTAudio.sec_to_str(self.length)

    @staticmethod
    def sec_to_str (sec_time) -> str:
        tim = int(sec_time)
        minutes = int(tim / 60) % 60
        hours = int(tim / 60 / 60) % 24  # uh
        seconds = tim % 60
        if hours == 0:
            return "%s:%s" % (YTAudio.two_digit(minutes), YTAudio.two_digit(seconds))
        else:
            return "%s:%s:%s" % (YTAudio.two_digit(hours), YTAudio.two_digit(minutes), YTAudio.two_digit(seconds))

    @staticmethod
    def two_digit (num: int) -> str:
        if num < 10:
            return "0%d"%num
        else:
            return str(num)


AUDIOS: List[YTAudio] = []
currently_playing = 0
is_playing = False
is_paused = False

# window setup ?
VLC = vlc.Instance()
PLAYER = VLC.media_player_new()
PLAYER.set_mrl('', ":no-video")


# PLAYLIST INITIALIZATION

def add_video(url):
    try:
        AUDIOS.append(YTAudio(url, vlc_instance=VLC, player=PLAYER))
        print('added %s'%AUDIOS[-1].title)
    except:
        print(f"aw. getting video {url} didn't work.")

def add_csv (filename):
    try:
        csv = open(filename, 'r').read()
    except FileNotFoundError:
        print('could not open %s'%filename)
        return
    lines = csv.split('\n')
    for l in lines:
        entries = l.split(',')
        if len(entries) == 0 or entries[0] == '':
            continue
        add_video(entries[0])

def add_playlist (url):
    playlist = pafy.get_playlist(url)
    for p in playlist['items']:
        url = p['pafy'].watchv_url
        add_video(url)


def shuffle():
    global AUDIOS, currently_playing
    get_current().stop()
    new_list = []
    while len(AUDIOS) > 0:
        aud = AUDIOS[random.randrange(len(AUDIOS))]
        new_list.append(aud)
        AUDIOS.remove(aud)

    AUDIOS = new_list
    currently_playing = 0


def start_playlist(repeat=False):
    global is_playing
    the_play = Thread(target=play, args=(repeat,))
    is_playing = True
    the_play.start()
    # this will pass through

def play(repeat=False):
    global currently_playing

    while is_playing:
        clip = get_current()
        print('starting: %s'%clip.title)
        clip.start()  # start the yt video
        while not clip.finished:
            time.sleep(0.1)
        currently_playing += 1
        if currently_playing >= len(AUDIOS):
            if repeat:
                currently_playing = 0 # restart playlist. callback?
            else:
                break  # end playback totally. callback?

    print('finished playing')
    stop()
    sys.exit()

# OTHER MANAGEMENT

def get_current () -> YTAudio:
    return AUDIOS[currently_playing]

def get_next () -> YTAudio:
    return AUDIOS[currently_playing + 1] # works because of list wrapping

# PLAYLIST CONTROL

def pause():
    global is_paused
    if is_paused:
        print('already paused!')
        return
    get_current().pause()
    is_paused = True
    print('paused at %s'%get_current().get_time())

def resume():
    global is_paused
    if not is_paused:
        print('already playing!')
        return
    get_current().resume()
    is_paused = False
    print('resumed')

def skip():
    get_current().stop()
    # print('skipped')

def skip_all():
    for a in AUDIOS:
        a.stop()

def soft_play():
    if not is_playing:
        start_playlist()
        print('decided to start playing from beginning')
    else:
        if is_paused:
            resume()
        elif not get_current().playing:
            get_current().start()

def stop():
    global is_playing
    for a in AUDIOS:
        a.stop()
    is_playing = False
    PLAYER.stop()
    print('stopped')

def restart():
    get_current().restart()
    print('restarted')

def moveto (*args):
    params = []
    for a in args:
        params.append(float(a))
    if len(params) == 1:
        get_current().set_time_sec(params[0])
        print('set time to <%s> seconds'%params[0])
    elif len(params) == 2:
        get_current().set_time_min_sec(params[0], params[1])
        print('set time to <%s> min, <%s> sec'%(params[0], params[1]))
    elif len(params) == 3:
        get_current().set_time_hour_min_sec(*params)
        print('set time to <%s> hours, <%s> min, <%s> sec'%(params[0], params[1], params[2]))
    else:
        print('bad parameters. move [hours] [minutes] <seconds>')

def rel (*args):
    params = []
    for a in args:
        params.append(float(a))
    if len(params) == 1:
        get_current().relative_set_sec(params[0])
        print('moved time <%s> seconds' % params[0])
    elif len(params) == 2:
        get_current().relative_set_min_sec(params[0], params[1])
        print('moved time <%s> min, <%s> sec' % (params[0], params[1]))
    elif len(params) == 3:
        get_current().relative_set_hour_min_sec(*params)
        print('moved time <%s> hours, <%s> min, <%s> sec' % (params[0], params[1], params[2]))
    else:
        print('bad parameters. rel [hours] [minutes] <seconds>')

def forward (*args):
    rel(*args)

def back (*args):
    ar = []
    for a in args:
        ar.append(-float(a))
    rel(*ar)

def check (*args):
    print('time: %s  %s'%(get_current().get_time(), ' '.join(args)))
    print('player is playing? %s'%get_current().player.is_playing())
    print('is playing? %s'%get_current().playing)
    print('is finished? %s'%get_current().finished)

# INFO

def list ():
    number:int = 0
    print('all clips:')
    for s in AUDIOS:
        print('%d. %s'%(number, s.title))
        number += 1

def goto (*args):
    global currently_playing
    index = int(args[0])
    if not 0 <= index < len(AUDIOS):
        print('%d is not a valid clip number. goto <num> WHERE 0 <= num <= %d'%(index, len(AUDIOS) - 1))
        return
    # print('going to clip %d: %s'%(index, AUDIOS[index].title))
    currently_playing = index - 1 # it will increment this when it finishes the song
    skip()

def info ():
    print('currently playing: %s'%get_current().title)
    print("time: %s, length: %s"%(get_current().get_time(), get_current().get_length()))
    print('next up: %s'%get_next().title)

def get_link ():
    url = get_current().yt_video_url
    has_q = url.find('?') >= 0
    time_url = url + ('&' if has_q else '?') + 't=%d'%int(get_current().current_time)
    print(f'video: {url}')
    print('video at current time: %s'%time_url)