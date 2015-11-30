import radio
import pygame
from radiosettings import SCREENS

def main():
    radio.init_session(tft=False, debug=True)
    radio.start()
    while True:
        radio.read_control(tft=False)
        if pygame.event.poll().type == pygame.QUIT:
            radio.terminate()

if __name__ == '__main__': main()
