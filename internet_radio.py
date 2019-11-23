import vlc
import threading
import csv
from transitions import Machine, State, MachineError

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class InternetRadio:

    states = [
        State(name='standby', on_enter='_on_enter_standby'),
        State(name='turning_on', on_enter='_on_enter_turning_on'),
        State(name='stopped', on_enter='_on_enter_stopped'),
        State(name='stopping', on_enter='_on_enter_stopping'),
        State(name='playing', on_enter='_on_enter_playing'),
        State(name='changing_channel_next', on_enter='_on_enter_changing_channel_next'),
        State(name='changing_channel_previous', on_enter='_on_enter_changing_channel_previous'),
        State(name='changing_channel', on_enter='_on_enter_changing_channel'),
        State(name='turning_off', on_enter='_on_enter_turning_off')
    ]

    transitions = [
        ['on', 'standby', 'turning_on'],
        ['on_complete', 'turning_on', 'stopped'],
        ['play', 'stopped', 'playing'],
        ['next', ['stopped', 'playing'], 'changing_channel_next'],
        ['previous', ['stopped', 'playing'], 'changing_channel_previous'],
        ['set', ['stopped', 'playing'], 'changing_channel'],
        ['channel_changed', 'changing_channel_next', 'playing'],
        ['channel_changed', 'changing_channel_previous', 'playing'],
        ['channel_changed', 'changing_channel', 'playing'],
        ['stop', 'playing', 'stopping'],
        ['done_stopping', 'stopping', 'stopped'],
        ['off', ['playing', 'stopped'], 'turning_off'],
        ['off_complete', 'turning_off', 'standby']
    ]

    current_station_index = 0

    def __init__(self, stations, event_queue):
        self.volume = 100
        self.stations = stations
        self.machine = Machine(model=self, states=self.states, transitions=self.transitions, initial='standby')
        self.event_queue = event_queue
        self.event_queue.put(InternetRadioInformation(self.state, self.stations[self.current_station_index].name))
    
    @threaded
    def _on_enter_standby(self):
        self.event_queue.put(InternetRadioInformation(self.state, ''))

    @threaded
    def _on_enter_turning_on(self):
        self.vlc = vlc.Instance('--input-repeat=-1', '--fullscreen')
        media_list = self.vlc.media_list_new([station.url for station in self.stations])
        self.player = self.vlc.media_list_player_new()
        self.player.set_media_list(media_list)
        self.player.set_playback_mode(vlc.PlaybackMode.loop)
        self._get_state()
        self.on_complete()

    @threaded
    def _on_enter_stopped(self):
        self.event_queue.put(InternetRadioInformation(self.state, self.stations[self.current_station_index].name))
        self.player.stop()

    @threaded
    def _on_enter_stopping(self):
        self.player.stop()
        self.done_stopping()

    @threaded
    def _on_enter_playing(self):
        self.event_queue.put(InternetRadioInformation(self.state, self.stations[self.current_station_index].name))
        self._set_volume(self.volume)
        self.player.play_item_at_index(self.current_station_index)

    @threaded
    def _on_enter_changing_channel_next(self):
        self.current_station_index = (self.current_station_index + 1) % len(self.stations)
        self.channel_changed()

    @threaded
    def _on_enter_changing_channel_previous(self):
        self.current_station_index = (self.current_station_index + len(self.stations) - 1) % len(self.stations)
        self.channel_changed()

    @threaded
    def _on_enter_changing_channel(self, station):
        self.current_station_index = self.stations.index(station)
        self.channel_changed()

    @threaded
    def _on_enter_turning_off(self):
        if self.player.is_playing:
            self.player.stop()
        self.player.release()
        self.player = None
        self.vlc = None
        self.off_complete()

    def _get_state(self):
        with open('state.csv') as radio_state_file:
            readCSV = csv.reader(radio_state_file, delimiter=',')
            for csv_radio_state in readCSV:
                self.current_station_index = int(csv_radio_state[1])

    def _set_volume(self, volume):
        self.volume = volume
        self.player.get_media_player().audio_set_volume(self.volume)

    def _persist_state(self):
        with open('state.csv', 'w') as radio_state_file:
            radio_state_file.write('current_station_index,%d' % self.current_station_index)

class InternetRadioInformation:
    def __init__(self, state, station_name):
        self.state = state
        self.station_name = station_name