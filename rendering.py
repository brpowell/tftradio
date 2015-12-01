from radiosettings import *


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

def draw_text(text, surface, surface_position, x, y, size=12):
    np_font = pygame.font.SysFont("Helvetica", size)
    lbl = np_font.render(text, 1, (255, 255, 255))
    text_pos = lbl.get_rect()
    text_pos.centerx = x
    text_pos.centery = y

    surface.blit(lbl, text_pos)
    screen.blit(surface, surface_position)
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
        btns.append('home-2x.png')

    img_x = 25
    for img_file in btns:
        path = os.path.join(session['IMAGES'], img_file)
        control_panel_surface.blit(pygame.image.load(path), (img_x, 0))
        img_x += 32
    screen.blit(control_panel_surface, (0, 223))
    pygame.display.flip()
    session['PANEL'] = panel

def render_stations():
    global screen, session
    header_surface = pygame.Surface((283, 20), pygame.SRCALPHA)
    background = pygame.image.load(os.path.join(session['IMAGES'], 'menu.png'))
    screen.blit(background, (0, 0))
    render_control_panel(PANELS.PAGES)
    draw_text('Select Station', header_surface, SS_POS, SS_WIDTH/2, 10)

    conn = sql.connect(session['DB'])
    stations = conn.execute("SELECT name FROM stations").fetchall()
    index = session['PAGE']*5

    station_y = 52
    for n in range(index-5, index):
        if n < len(stations):
            draw_text(stations[n][0], screen, (0, 0), 160, station_y, size=16)
            station_y += 36
        else:
            break

    pygame.display.flip()
    session['SCREEN'] = SCREENS.STATIONS


def render_home():
    global screen, session
    header_surface = pygame.Surface((283, 20), pygame.SRCALPHA)

    img_files = ['home.png', 'musical-note-8x.png', 'rss-alt-8x.png',
            'spreadsheet-8x.png', 'cog-8x.png']
    imgs = []
    for n in range(0, 5):
        imgs.append(pygame.image.load(os.path.join(session['IMAGES'], img_files[n])))
    screen.blit(imgs[0], (0, 0))

    draw_text('Now Playing', screen, (0, 0), 82, 112)
    screen.blit(imgs[1], (50, 40))
    draw_text('Stations', screen, (0, 0), 232, 114)
    screen.blit(imgs[2], (200, 40))
    draw_text('History', screen, (0, 0), 82, 206)
    screen.blit(imgs[3], (50, 140))
    draw_text('System', screen, (0, 0), 232, 207)
    screen.blit(imgs[4], (200, 136))
    draw_text(session['CURRENT_TRACK']['station'], header_surface,
            SS_POS, SS_WIDTH/2, 10)
    render_control_panel(PANELS.MEDIA)
    pygame.display.flip()
    session['SCREEN'] = SCREENS.HOME

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
        session['CURRENT_TRACK'] = { 'song': tracks[0][1],
        'artist': tracks[0][2], 'album': tracks[0][3], 'station': tracks[0][4],
        'art': tracks[0][5] }

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

    RENDER_EV.set()

    render_control_panel(PANELS.MEDIA)
    pygame.display.flip()
    session['SCREEN'] = SCREENS.NOWPLAYING
    t_nowplaying = threading.Thread(target=render_nowplaying_thread)
    t_nowplaying.start()
