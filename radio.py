from radiosettings import *
from rendering import *
import pygame

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
        pygame.display.set_caption('TFT Radio')
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

def read_control(tft=False):
    global session

    # Screen touches
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            print(pos)
            if session['SCREEN'] == SCREENS.NOWPLAYING:
                if 262 <= pos[0] <= 310 and 100 <= pos[1] <= 148:
                    panel = 0
                    if session['PANEL'] == PANELS.VOLUME:
                        panel = PANELS.MEDIA
                    elif session['PANEL'] == PANELS.MEDIA:
                        panel = PANELS.VOLUME
                    render_control_panel(panel)
                elif 262 <= pos[0] <= 310 and 45 <= pos[1] <= 93:
                    render_home()
                    RENDER_EV.set()
            elif session['SCREEN'] == SCREENS.HOME:
                if 50 <= pos[0] <= 114 and 40 <= pos[1] <= 104:
                    render_nowplaying()
                elif 200 <= pos[0] <= 264 and 40 <= pos[1] <= 104:
                    render_stations()
            elif session['SCREEN'] == SCREENS.STATIONS:
                index = session['PAGE']*5
                if 30 <= pos[0] <= 292 and 38 <= pos[1] <= 66:
                    index -= 5
                elif 30 <= pos[0] <= 292 and 73 <= pos[1] <= 101:
                    index -= 4
                elif 30 <= pos[0] <= 292 and 108 <= pos[1] <= 136:
                    index -= 3
                elif 30 <= pos[0] <= 292 and 143 <= pos[1] <= 171:
                    index -= 2
                elif 30 <= pos[0] <= 292 and 178 <= pos[1] <= 106:
                    index -= 1
                else:
                    return
                print(index)
                fifo = os.path.join(session['PIANOBAR'], 'ctl')
                cmd = 'echo s%d > %s &' % (index, fifo)
                os.system(cmd)

            # elif session['SCREEN'] == SCREENS.HOME:
            #     if 193 <= pos[0] <= 257 and 44 <= pos[1] <= 108:
            # square_surface = pygame.Surface((48, 48), pygame.SRCALPHA)


    # Button presses
    if tft:
        if session['PANEL'] == PANELS.VOLUME:
            if pitft.Button1:
                control_pianobar('audio down')
            elif pitft.Button2:
                control_pianobar('audio up')
            elif pitft.Button3:
                control_pianobar('audio mute')
        elif session['PANEL'] == PANELS.MEDIA:
            if pitft.Button1:
                control_pianobar('p')
            elif pitft.Button2:
                control_pianobar('next')
            elif pitft.Button3:
                control_pianobar('love')
            elif pitft.Button4:
                control_pianobar('hate')
        elif session['PANEL'] == PANELS.PAGES:
            if pitft.Button3:
                render_home()
            else:
                if pitft.Button1 and session['PAGE'] > 0:
                    session['PAGE'] -= 1
                elif pitft.Button2 and session['PAGE'] < session['PAGE']*5-1:
                    session['PAGE'] += 1
                render_stations()


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
    t_new_track = threading.Thread(target=new_track_thread)
    t_new_track.start()

def terminate():
    global session
    session['ACTIVE'] = False
    raise SystemExit
