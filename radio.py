from components import *

def main():
    global screen, session

    init_session(tft=False, debug=True)
    start()

    while True:
        read_control(tft=False)
        if pygame.event.poll().type == pygame.QUIT:
            terminate()

if __name__ == '__main__': main()
