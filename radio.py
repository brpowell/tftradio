from components import *

def main():
    global screen, session
    os.putenv('SDL_FBDEV', '/dev/fb1')  # Use TFT
    session['DEBUG'] = True
    pygame.init()
    screen = pygame.display.set_mode((320, 240))
    # pygame.mouse.set_visible(False)
    init_session()
    start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if 262 <= pos[0] <= 310 and 100 <= pos[1] <= 148:
                    toggle_control_panel()
                # if 262 <= pos[0] <= 310 and 104 <= pos[1] <= 152:
                #     print('yup')

        # if show_volume_control:
        #     if pitft.Button1:
        #         control_pianobar('audio down')
        #     if pitft.Button2:
        #         control_pianobar('audio up')
            # if pitft.Button3:
            #     control_pianobar('audio mute')
        # else:
        #     if pitft.Button1:
        #         control_pianobar('p')
        #     if pitft.Button2:
        #         control_pianobar('next')
        #     if pitft.Button3:
        #         control_pianobar('love')
        #     if pitft.Button4:
        #         control_pianobar('hate')

        if pygame.event.poll().type == pygame.QUIT:
            terminate()

if __name__ == '__main__': main()
