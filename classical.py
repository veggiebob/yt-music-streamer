import audio_manager, commands, sys

audio_manager.load_from_playlist('https://www.youtube.com/playlist?list=PLTfTRP_g2I3QQYS-WT_OtjxowNdvJlCFZ')
audio_manager.shuffle()
audio_manager.start_playlist(repeat=True)

while audio_manager.is_playing:
    hey = input()
    commands.process_command(hey)

sys.exit()