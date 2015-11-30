import os
import pygame
import sqlite3 as sql
import threading
from time import sleep

session = { "IMAGES": None, "CONTROL": None, "PIANOBAR": None, "ACTIVE": True,
            "VOLUME_CONTROL": None, "VOLUME": 100, "MUSIC_PLAYING": False,
            "CURRENT_TRACK": None, "DEBUG": False, 'PANEL': 0, 'SCREEN': None }
screen = pygame.display.set_mode((320, 240))
pitft = 0

# EVENTS - thread control
NEW_TRACK_EV = threading.Event()
RENDER_EV = threading.Event()

# COLORS
BG_COLOR = (23, 148, 207)
INFO_COLOR = (32, 85, 134)
HEADER_COLOR = (19, 52, 82)

# IS: Info Surface
IS_WIDTHWIDTH = 283
IS_WIDTHHEIGHT = 58
IS_WIDTHPOS = (19, 161)
# SS: Status Surface
SS_WIDTH = 283
SS_HEIGHT = 20
SS_POS = (19, 7)

def enum(**enums):
    return type('Enum', (), enums)

PANELS = enum(MEDIA=0, VOLUME=1, PAGES=2)
SCREENS = enum(NOWPLAYING=0, HOME=1, STATIONS=2)

def debug(message):
    global session
    if session['DEBUG']:
        print message

def init_session(pianobar='/home/bryan/.config/pianobar', tft=True, debug=False):
    global session, screen, pitft
    local_path = os.path.dirname(os.path.realpath(__file__))

    if tft:
        from pitftscreen import pitft
        os.putenv('SDL_FBDEV', '/dev/fb1')
        pygame.init()
        pygame.mouse.set_visible(False)
        pitft = PiTFT_Screen()
    else:
        pygame.init()

    screen = pygame.display.set_mode((320, 240))
    session['PIANOBAR'] = pianobar
    session['IMAGES'] = os.path.join(local_path, 'images')
    session['CONTROL'] = os.path.join(pianobar, 'control-pianobar.sh')
    session['DB'] = os.path.join(local_path, 'radio.db')
    session['DEBUG'] = debug

    create_new_db = not os.path.exists(session['DB'])
    conn = sql.connect(session['DB'])
    if create_new_db:
        conn.execute("CREATE TABLE history ( \
        id integer primary key, song text, artist text, \
        album text, station text, art text)")
    else:
        conn.execute("DROP TABLE stations")

    # Populate stations table
    conn.execute("CREATE TABLE stations (id integer, name text)")
    stations_file = os.path.join(session['PIANOBAR'], 'stationlist')
    with open(stations_file) as stations:
        for line in stations:
            station_info = line.split(')')
            station_id = int(station_info[0])
            station_name = station_info[1].lstrip().rstrip(' Radio\n')
            conn.execute("INSERT INTO stations(id, name) VALUES(?, ?)",
            (station_id, station_name))
        conn.commit()

def flash_status(command):
    global session
    status = ''
    if command == 'p':
        if music_playing:
            status = 'play'
        else:
            status = 'pause'
    elif command == 'next':
        status = 'Skipping track...'
    elif command == 'love':
        status = 'Track liked'
    elif command == 'hate':
        status = 'Track disliked'

    header_surface = pygame.Surface((283, 20), pygame.SRCALPHA)
    header_surface.fill(HEADER_COLOR)
    draw_text(status, header_surface, SS_POS, SS_WIDTH/2, 10)
    sleep(5)
    station = session['CURRENT_TRACK']['station']
    draw_text(station, header_surface, SS_POS, SS_WIDTH/2, 10)

def control_pianobar(command):
    global session
    volume = session['VOLUME']

    if command.split(' ')[0] == 'audio':
        arg = command.split(' ')[1]
        if arg == 'up' and audio_level < 100:
            volume += 2
        elif arg == 'down' and volume > 50:
            volume -= 2
        elif arg == 'set':
            volume = int(command.split(' ')[2])
        os.system('amixer sset PCM,0 ' + str(volume) + '%')
        session['VOLUME'] = volume
    else:
        if(command == 'p'):
            session['MUSIC_PLAYING'] = not session['MUSIC_PLAYING']
        status = Thread(target=flash_status, args=(command,))
        status.start()
        os.system('su pi -c \"' + session['CONTROL'] + command + '\"')

def draw_text(text, surface, surface_position, x, y):
    np_font = pygame.font.SysFont("Helvetica", 12)
    lbl = np_font.render(text, 1, (255, 255, 255))
    text_pos = lbl.get_rect()
    text_pos.centerx = x
    text_pos.centery = y

    surface.blit(lbl, text_pos)
    screen.blit(surface, surface_position)
    pygame.display.flip()

def render_home():
    global screen
    header_surface = pygame.Surface((283, 20), pygame.SRCALPHA)
    background = pygame.image.load(os.path.join(session['IMAGES'], 'home.png'))
    screen.blit(background, (0, 0))
    pygame.display.flip()

def render_nowplaying_thread():
    global screen
    global NEW_TRACK_EV, RENDER_EV

    conn = sql.connect(session['DB'])
    while session['ACTIVE'] and session['SCREEN'] == SCREENS.NOWPLAYING:
        debug('render_thread: Waiting')
        RENDER_EV.wait()
        RENDER_EV.clear()
        if not session['ACTIVE'] or session['SCREEN'] != SCREENS.NOWPLAYING:
            debug('render_thread: Exited')
            return
        debug('render_thread: Waited')

        tracks = conn.execute("SELECT * FROM history \
                                ORDER BY id DESC LIMIT 3").fetchall()

        # Render album images
        album_surfaces = []
        album_surfaces.append(pygame.Surface((110, 110), pygame.SRCALPHA))
        album_surfaces.append(pygame.Surface((90, 90), pygame.SRCALPHA))
        album_surfaces.append(pygame.Surface((68, 68), pygame.SRCALPHA))

        if len(tracks) == 3:
            album_image_3 = pygame.image.load(tracks[2][5])
            album_image_3 = pygame.transform.scale(album_image_3, (68, 68))
            album_image_3.set_alpha(100)
            album_surfaces[2].fill(BG_COLOR)
            album_surfaces[2].blit(album_image_3, (2, 2))
        if len(tracks) >= 2:
            album_image_2 = pygame.image.load(tracks[1][5])
            album_image_2 = pygame.transform.scale(album_image_2, (90, 90))
            album_image_2.set_alpha(160)
            album_surfaces[1].fill(BG_COLOR)
            album_surfaces[1].blit(album_image_2, (2, 2))

        album_image = pygame.image.load(tracks[0][5])
        album_image = pygame.transform.scale(album_image, (106, 106))
        album_surfaces[0].fill((0, 0, 0))
        album_surfaces[0].blit(album_image, (2, 2))

        screen.blit(album_surfaces[2], (178, 59))
        screen.blit(album_surfaces[1], (108, 49))
        screen.blit(album_surfaces[0], (18, 39))

        # Render header and track info
        header_surface = pygame.Surface((283, 20), pygame.SRCALPHA)
        header_surface.fill(HEADER_COLOR)
        info_surface = pygame.Surface((283, 58), pygame.SRCALPHA)
        info_surface.fill(INFO_COLOR)
        draw_text(tracks[0][1], info_surface, IS_WIDTHPOS, IS_WIDTHWIDTH/2, 13)
        draw_text(tracks[0][2], info_surface, IS_WIDTHPOS, IS_WIDTHWIDTH/2, IS_WIDTHHEIGHT/2)
        draw_text(tracks[0][3], info_surface, IS_WIDTHPOS, IS_WIDTHWIDTH/2, 46)
        draw_text(tracks[0][4], header_surface, SS_POS, SS_WIDTH/2, 10)

        pygame.display.flip()

        NEW_TRACK_EV.set()
    debug('render_thread: Exited')

def render_nowplaying():
    global screen

    background_image = os.path.join(session['IMAGES'], 'nowplaying.png')
    background = pygame.image.load(background_image)
    volume_btn = pygame.image.load(os.path.join(session['IMAGES'], 'volume-high-6x.png'))
    volume_btn = pygame.transform.scale(volume_btn, (42, 42))
    home_btn = pygame.image.load(os.path.join(session['IMAGES'], 'home-6x.png'))
    home_btn = pygame.transform.scale(home_btn, (42, 42))
    screen.blit(background, (0, 0))
    screen.blit(volume_btn, (262, 105))
    screen.blit(home_btn, (262, 45))
    pygame.display.flip()

def render_control_panel(panel, hide=False):
    global session

    control_panel_surface = pygame.Surface((320, 16), pygame.SRCALPHA)
    control_panel_surface.fill(BG_COLOR)
    if hide:
        pygame.display.flip()
        return

    btns = []
    if panel == PANELS.MEDIA:
        play_pause = ''
        if session['MUSIC_PLAYING']:
            play_pause = 'pause-2x.png'
        else:
            play_pause = 'play-2x.png'
        btns.append(play_pause)
        btns.append('skip-2x.png')
        btns.append('like-2x.png')
        btns.append('dislike-2x.png')
    elif panel == PANELS.VOLUME:
        btns.append('volume-low-2x.png')
        btns.append('volume-high-2x.png')
        btns.append('volume-off-2x.png')
    elif panel == PANELS.PAGES:
        btns.append('arrow-thick-left-2x.png')
        btns.append('arrow-thick-right-2x.png')

    img_x = 25
    for img_file in btns:
        path = os.path.join(session['IMAGES'], img_file)
        control_panel_surface.blit(pygame.image.load(path), (img_x, 0))
        img_x += 32
    screen.blit(control_panel_surface, (0, 223))
    pygame.display.flip()
    session['PANEL'] = panel

def read_control(tft=False):
    global session

    # Screen touches
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if session['SCREEN'] == SCREENS.NOWPLAYING:
                if 262 <= pos[0] <= 310 and 100 <= pos[1] <= 148:
                    panel = 0
                    if session['PANEL'] == PANELS.VOLUME:
                        panel = PANELS.MEDIA
                    elif session['PANEL'] == PANELS.MEDIA:
                        panel = PANELS.VOLUME
                    render_control_panel(panel)

    # Button presses
    if tft:
        if session['PANEL'] == PANELS.VOLUME:
            if pitft.Button1:
                control_pianobar('audio down')
            if pitft.Button2:
                control_pianobar('audio up')
            if pitft.Button3:
                control_pianobar('audio mute')
        elif session['PANEL'] == PANELS.MEDIA:
            if pitft.Button1:
                control_pianobar('p')
            if pitft.Button2:
                control_pianobar('next')
            if pitft.Button3:
                control_pianobar('love')
            if pitft.Button4:
                control_pianobar('hate')

def new_track_thread():
    global session
    global NEW_TRACK_EV, RENDER_EV

    debug('new_track_thread: Running')
    conn = sql.connect(session['DB'])

    while session['ACTIVE']:
        new_track_path = os.path.join(session['PIANOBAR'], 'newtrack')
        new_track = os.path.exists(new_track_path)
        if new_track:
            os.remove(new_track_path)
            # Get album and radio station
            album_station_path = os.path.join(session['PIANOBAR'], 'durationstation')
            lines = [line.rstrip('\n') for line in open(album_station_path)]
            album = lines[1].replace('Album: ', '')
            station = lines[2].replace('Station: ', '')

            # Get artist and song
            artist_song_path = os.path.join(session['PIANOBAR'], 'nowplaying')
            with open(artist_song_path) as f:
                lines = f.readline().rstrip().split(' - ')
            artist = lines[0]
            song = lines[1]

            # Get art
            art_path = os.path.join(session['PIANOBAR'], 'artname')
            with open(art_path, 'r') as art_file:
                art = art_file.readline().rstrip('\n')

            # Cache current track and insert into database
            sql_cmd = "INSERT INTO history (song, artist, album, station, art) VALUES(?, ?, ?, ?, ?)"
            conn.execute(sql_cmd, (song, artist, album, station, art))
            conn.commit()
            session['CURRENT_TRACK'] = { 'song': song, 'artist': artist,
            'album': album, 'station': station, 'art': art }

            RENDER_EV.set()
            NEW_TRACK_EV.wait()
            NEW_TRACK_EV.clear()

    RENDER_EV.set()
    debug('new_track_thread: Exited')

def start():
    render_nowplaying()
    render_control_panel(PANELS.MEDIA)
    t_new_track = threading.Thread(target=new_track_thread)
    t_new_track.start()
    t_nowplaying = threading.Thread(target=render_nowplaying_thread)
    t_nowplaying.start()
    session['SCREEN'] = SCREENS.NOWPLAYING

def terminate():
    global session
    session['ACTIVE'] = False
    raise SystemExit
