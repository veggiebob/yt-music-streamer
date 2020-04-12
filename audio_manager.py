import os
import random
import time
from threading import Thread
from typing import List, Dict

from pafy.backend_youtube_dl import YtdlPafy

os.add_dll_directory("C:\Program Files (x86)\VideoLAN\VLC") # this is windows specific. you need a vlc


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
        self.finished = True
        self.paused = False

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

        self.player.set_media(self.media)
        self.player.play()
        self.playing = True
        self.paused = False
        play = Thread(target=self.play_continuous)
        play.start()
        play.join(timeout=self.length)

    def play_continuous(self) -> None:
        # curr_time = time.perf_counter()
        while self.playing:
            # now_time = time.perf_counter()
            # if now_time - curr_time > self.length:
            #     break
            while self.paused:
                time.sleep(1.0)

        self.finished = True

    def pause(self):
        self.player.pause()
        self.paused = True

    def resume(self):
        self.player.play()
        self.paused = False

    def stop(self):
        self.player.stop()
        self.playing = False
        self.finished = True

    def restart (self):
        self.player.set_media(self.media)
        self.player.play()


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
    AUDIOS.append(YTAudio(url, vlc_instance=VLC, player=PLAYER))

def load_from_csv (filename):
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

def load_from_playlist (url):
    playlist = pafy.get_playlist(url)
    for p in playlist['items']:
        url = p['pafy'].watchv_url
        add_video(url)


def shuffle():
    global AUDIOS
    new_list = []
    while len(AUDIOS) > 0:
        aud = AUDIOS[random.randrange(len(AUDIOS))]
        new_list.append(aud)
        AUDIOS.remove(aud)

    AUDIOS = new_list


def start_playlist(repeat=False):
    global is_playing
    the_play = Thread(target=play, args=(repeat,))
    is_playing = True
    the_play.start()
    # this will pass through

def play(repeat=False):
    global currently_playing

    while is_playing:
        clip = AUDIOS[currently_playing]
        print('starting %s'%clip.title)
        clip.start()  # start the yt video
        while not clip.finished:
            time.sleep(0.5)
        currently_playing += 1
        if currently_playing >= len(AUDIOS):
            if repeat:
                currently_playing = 0 # restart playlist. callback?
            else:
                break  # end playback totally. callback?

    print('finished playing')
    stop()

# PLAYLIST CONTROL

def pause():
    global is_paused
    AUDIOS[currently_playing].pause()
    is_paused = True
    print('paused')


def resume():
    global is_paused
    if is_playing:
        print('already playing!')
        return
    AUDIOS[currently_playing].resume()
    is_paused = False
    print('resumed')


def skip():
    AUDIOS[currently_playing].stop()
    print('skipped')

def soft_play():
    if not is_playing:
        start_playlist()
        print('decided to start playing from beginning')
    else:
        if is_paused:
            resume()
        else:
            return

def stop():
    global is_playing
    for a in AUDIOS:
        a.stop()
    is_playing = False
    PLAYER.stop()
    print('stopped')

def restart():
    AUDIOS[currently_playing].restart()
    print('restarted')
