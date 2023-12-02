"""The PAM245 integration."""
import asyncio
import logging

import serial_asyncio

_LOGGER = logging.getLogger(__name__)

SWITCH_COMMANDS = {
    'mute': 'Mute',
    'power': 'Power',
    'system_lock': 'Lock',
    'zone_all': 'Zone 0',
    'zone_1': 'Zone 1',
    'zone_2': 'Zone 2',
    'zone_3': 'Zone 3',
    'zone_4': 'Zone 4',
    'zone_5': 'Zone 5',
    }

SWITCH_EVENTS = {
    'Mute': 'mute',
    'Power': 'power',
    'Lock': 'system_lock',
    }

class PAM245Api:
    VOLUME_MIN = 0
    VOLUME_MAX = 79
    VOLUME_STEP = 3

    def __init__(self) -> None:
        # Read/write
        self.volume = 0
        self.mute = False
        self.power = True
        self.system_lock = False
        self.zone_all = False
        self.zone_1 = False
        self.zone_2 = False
        self.zone_3 = False
        self.zone_4 = False
        self.zone_5 = False

        # Read only
        self.firmware_version = "0.0.todo"
        self.serial = "TODOserialnumber"

        # Other
        self.available = False
        self._callbacks = set()
        self._unparsed = ''

    def event_connection_made(self, send_data_fn):
        self._send_data_to_device = send_data_fn
        self.available = True
        self._call_callbacks() # Advertise availability

        # Make sure no half-typed commands from previous sessions
        # interfere with the next commands
        self._send_command('')

        # Reset device state
        self._send_command('Version') # Get firmware version
        self._send_command('Now') # Get current state

    def event_connection_lost(self, send_data_fn):
        self._send_data_to_device = None
        self.available = False
        self._call_callbacks() # Advertise unavailability

    def set_volume(self, volume: int) -> None:
        if self.VOLUME_MIN <= volume <= self.VOLUME_MAX:
            self.volume = volume
            _LOGGER.info(f"Set volume to {volume}")
            self._send_command(f"Volume {volume:02}")
        else:
            _LOGGER.warning(f"Commanded volume out of range ({volume})")

    def set_switch(self, key: str, value: bool) -> None:
        setattr(self, key, value)
        _LOGGER.info(f"Set {key} to {value}")
        self._send_command(f"{SWITCH_COMMANDS[key]} {1 if value else 0}")

    def add_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.discard(callback)

    def _process_events_from_device(self, events):
        for event in events:
            match event:
                case ['PA', date, version]:
                    self.firmware_version = f"PA {date} {version}"
                case ['Volume', volume_str]:
                    volume = int(volume_str)
                    self._event_volume(volume)
                case ['Zone', zone_id, 'Out', value_str]:
                    if zone_id == 'All':
                        zone_id = 'all'
                    value = True if value_str == 'On' else False
                    self._event_switch(f'zone_{zone_id}', value)
                case [event_type, value_str] if event_type in SWITCH_EVENTS:
                    key = SWITCH_EVENTS[event_type]
                    value = True if value_str == 'On' else False
                    self._event_switch(key, value)
                case _:
                    unknown_event = ' '.join(event)
                    _LOGGER.warning(f'Unknown event: {unknown_event}')

    def _event_volume(self, volume):
        if self.VOLUME_MIN <= volume <= self.VOLUME_MAX:
            self.volume = volume
            self._call_callbacks()
        else:
            _LOGGER.warning(f"Event volume out of range ({volume})")

    def _event_switch(self, key, value):
        setattr(self, key, value)
        self._call_callbacks()

    def _call_callbacks(self):
        for callback in self._callbacks:
            callback()

    def _send_command(self, command):
        if self._send_data_to_device:
            data = (command+'\r\n').encode()
            self._send_data_to_device(data)
        else:
            _LOGGER.error(f'Command dropped (no connection): "{command}"')

    def parse_data_from_device(self, data):
        unparsed = self._unparsed + data.decode()
        events, self._unparsed = self.split_events(unparsed)
        _LOGGER.info(f"{events=} {self._unparsed=}")
        self._process_events_from_device(events)

    @staticmethod
    def split_events(unparsed):
        events = []
        while True:
            try:
                nl = unparsed.index("\n")
            except ValueError:
                break
            line, unparsed = unparsed[:nl], unparsed[nl+1:]
            events.append(line.split())
        return events, unparsed


class PAM245Protocol(asyncio.BaseProtocol):
    def __init__(self, api: PAM245Api):
        self._transport = None
        self.api = api
        super().__init__()

    def connection_made(self, transport):
        self._transport = transport
        self.api.event_connection_made(self.send_data)
        super().connection_made(transport)

    def connection_lost(self, exc):
        self._transport = None
        self.api.event_connection_lost()
        super().connection_lost(exc)

    def send_data(self, data):
        raise NotImplementedError

    def pam245_data_received(self, data):
        _LOGGER.info(f"Received data {data!r}")
        self.api.parse_data_from_device(data)


class PAM245AsyncConnection:
    def __init__(self):
        self.api = PAM245Api()
        self._transport = None

    def _start(self, transport):
        assert transport is not None
        assert self._transport is None
        self._transport = transport

    def stop(self):
        self._transport.close()
        self._transport = None


class PAM245SerialProtocol(PAM245Protocol, asyncio.Protocol):
    def __init__(self, api: PAM245Api):
        super().__init__(api)

    def data_received(self, data):
        _LOGGER.debug(f"Received serial data {data!r}")
        super().pam245_data_received(data)

    def send_data(self, data):
        self._transport.write(data)


class PAM245AsyncSerialConnection(PAM245AsyncConnection):
    async def start(self, loop, serial_port: str):
        transport, protocol = await serial_asyncio.create_serial_connection(
                loop,
                lambda: PAM245SerialProtocol(self.api),
                serial_port)
        self._start(transport)


class PAM245DatagramProtocol(PAM245Protocol, asyncio.DatagramProtocol):
    def __init__(self, tx_port: int, api: PAM245Api):
        self._tx_port = tx_port
        super().__init__(api)

    def datagram_received(self, data, addr):
        _LOGGER.debug(f"Received datagram {data!r} from {addr}")
        super().pam245_data_received(data)

    def send_data(self, data):
        self._transport.sendto(data, ('localhost', self._tx_port))


class PAM245AsyncUdpConnection(PAM245AsyncConnection):
    async def start(self, loop, rx_port: int, tx_port: int):
        transport, protocol = await loop.create_datagram_endpoint(
                lambda: PAM245DatagramProtocol(tx_port, self.api),
                ('localhost', rx_port))
        self._start(transport)
