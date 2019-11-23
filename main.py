import csv
import threading
import curses
import queue
import time
from radio_station import RadioStation
from internet_radio import InternetRadio
from transitions import MachineError
from curses import wrapper

def read_stations():
    stations = []
    with open('stations_list.csv') as radio_stations_file:
        readCSV = csv.reader(radio_stations_file, delimiter=',')
        for csv_station in readCSV:
            stations.append(RadioStation.fromCSV(csv_station))
    return stations

def user_input_thread_function(stdscr, internet_radio):
    while True:
        try:
            key = stdscr.getkey()
            if key == 'o':
                internet_radio.on()
            if key == 'x':
                internet_radio.off()
            if key == 'p':
                internet_radio.play()
            if key == 's':
                internet_radio.stop()
            if key == 'n':
                internet_radio.next()
            if key == 'b':
                internet_radio.previous()
        except MachineError as e:
            pass
        time.sleep(0.2)

def draw_static_gui():
    controls_win = curses.newwin(4, curses.COLS - 2, 1, 1)
    controls_win.border()
    controls_win.addstr(0, 2, 'Internet Radio')
    controls_win.addstr(2, 2, 'Controls: o - On | x - Off | p - Play | s - Stop | n - Next | b - Previous')
    controls_win.refresh()

def draw_dynamic_gui(stdscr, event_queue, stations):
    default_win = curses.newwin(curses.LINES - 5, curses.COLS - 2, 5, 1)
    while True: # Ugly solution(?) to avoid screen refresh bugs
        if not event_queue.empty():
            radio_information = event_queue.get()
            is_on = radio_information.state != 'standby'
            default_win.clear()
            default_win.border()
            default_win.addstr(0, 2, 'ON' if is_on else 'OFF', curses.color_pair(2) if is_on else curses.color_pair(4))
            
            default_win.addstr(2, 2, 'Radio Stations')
            station_row = 3
            for station in stations:
                if station.name == radio_information.station_name:
                    if radio_information.state == 'playing':
                        default_win.addstr(station_row, 3, '{}'.format(radio_information.station_name), curses.color_pair(2))
                    elif radio_information.state == 'stopped':
                        default_win.addstr(station_row, 3, '{}'.format(radio_information.station_name), curses.color_pair(3))
                    else:
                        default_win.addstr(station_row, 3, '{}'.format(station.name), curses.color_pair(1))
                else:
                    default_win.addstr(station_row, 3, '{}'.format(station.name), curses.color_pair(1))
                station_row = station_row + 1

            default_win.addstr(curses.LINES - 8, 2, 'State: {}'.format(radio_information.state))
            default_win.addstr(curses.LINES - 7, 2, '')
            default_win.refresh()
        time.sleep(0.05)

def draw_gui(stdscr, event_queue, stations):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, 7, -1) # White
    curses.init_pair(2, 2, -1) # Green
    curses.init_pair(3, 3, -1) # Yellow
    curses.init_pair(4, 1, -1) # Red
    draw_static_gui()
    draw_dynamic_gui(stdscr, event_queue, stations)

def initialize(stdscr):
    event_queue = queue.Queue()
    stations = read_stations()
    user_input_thread = threading.Thread(target=user_input_thread_function, args=(stdscr, InternetRadio(stations, event_queue)))
    user_input_thread.start()
    draw_gui(stdscr, event_queue, stations)
    
if __name__ == '__main__':
    wrapper(initialize)
