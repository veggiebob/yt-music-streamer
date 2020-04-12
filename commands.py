import audio_manager

COMMANDS = {
    'pause': audio_manager.pause,
    'skip': audio_manager.skip,
    'resume': audio_manager.resume,
    'play': audio_manager.soft_play,
    'restart': audio_manager.restart,
    'stop': audio_manager.stop
}

def process_command (command:str):
    command = command.lower().rstrip()
    if command in COMMANDS:
        COMMANDS[command]() # do the command
    else:
        print('%s is not a valid command'%command)