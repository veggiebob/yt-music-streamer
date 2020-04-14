import audio_manager, commands, sys

print('creating playlist . . .')
audio_manager.add_playlist('https://www.youtube.com/playlist?list=PLTfTRP_g2I3SiIEej6tWzvDc0uWiz_icx') # energetic classical
audio_manager.add_playlist('https://www.youtube.com/playlist?list=PLTfTRP_g2I3QQYS-WT_OtjxowNdvJlCFZ') # classical favs
# audio_manager.add_playlist('https://www.youtube.com/watch?v=YD9QvvhI6Sk&list=PL7CFEF478E3980B62') # mario galaxy
audio_manager.start_playlist()

while audio_manager.is_playing:
    commands.process_command(input())