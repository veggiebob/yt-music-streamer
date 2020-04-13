import audio_manager

def help ():
    global COMMANDS
    print('Here are all the commands:')
    for com in COMMANDS.keys():
        print("==> %s"%com)

COMMANDS = {
    'help': help,
    'play': audio_manager.soft_play,
    'move': audio_manager.moveto,
    'auto': 'info,goto,list,rel,back,forward,check,stop,restart,resume,skip,pause'.split(',')
}
for a in COMMANDS['auto']:
    if a in COMMANDS.keys():
        continue
    if hasattr(audio_manager, a):
        COMMANDS[a] = getattr(audio_manager, a)

def process_command (input_text:str):
    input_text = input_text.lower().strip()
    commands = input_text.split(' ')
    command = commands[0] # command name
    if len(commands) > 1:
        args = commands[1:]
    else:
        args = []
    if command in COMMANDS:
        try:
            COMMANDS[command](*args) # do the command
        except:
            COMMANDS[command]()
    else:
        print('%s is not a valid command' % command)