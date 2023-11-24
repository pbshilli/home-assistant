"""The PAM245 integration."""
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

SWITCH_COMMANDS = {
    'volume': 'Volume',
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
SWITCH_COMMANDS_REVERSE = {v:k for k, v in SWITCH_COMMANDS.items()}

class PAM245Api:
    VOLUME_MIN = 0
    VOLUME_MAX = 79

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
        self.available = True
        self._callbacks = set()
        self._unparsed = ''

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
                case ['Volume', volume_str]:
                    volume = int(volume_str)
                    self._event_volume(volume)
                case ['Zone', zone_id, value_str]:
                    if zone_id == '0':
                        zone_id = 'all'
                    value = bool(int(value_str))
                    self._event_switch(f'zone_{zone_id}', value)
                case [event_type, value_str] if event_type in SWITCH_COMMANDS_REVERSE:
                    key = SWITCH_COMMANDS_REVERSE[event_type]
                    value = bool(int(value_str))
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
        data = (command+'\n').encode()
        self.send_data_to_device(data)

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
        self.api = api
        super().__init__()

    def connection_made(self, transport):
        self.api.available = True
        super().connection_made(transport)

    def connection_lost(self, exc):
        self.api.available = False
        super().connection_lost(exc)

    def send_data(self, data):
        raise NotImplementedError

    def pam245_data_received(self, data):
        _LOGGER.info(f"Received data {data!r}")
        self.api.parse_data_from_device(data)


class PAM245SerialProtocol(PAM245Protocol, asyncio.Protocol):
    def __init__(self, api: PAM245Api):
        super().__init__(api)

    def connection_made(self, transport):
        self.transport = transport

        # TODO make sure hardware flow control doesn't interfere
        ser = self.transport.serial
        _LOGGER.warning(f"{ser.rtscts=} {ser.dsrdtr=}")

        super().connection_made(transport)

    def data_received(self, data):
        _LOGGER.debug(f"Received serial data {data!r}")
        super().pam245_data_received(data)

                    
class PAM245DatagramProtocol(PAM245Protocol, asyncio.DatagramProtocol):
    def __init__(self, api: PAM245Api):
        super().__init__(api)

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        _LOGGER.debug(f"Received datagram {data!r} from {addr}")
        super().pam245_data_received(data)


async def start_serial_connection(loop, api, serial_port):
    transport, protocol = await pyserial_asyncio.create_serial_connection(
            loop,
            lambda: PAM245SerialProtocol(api),
            serial_port)

    def send_data(data):
        transport.write(data)

    api.send_data_to_device = send_data

    return transport


async def start_datagram_connection(loop, api, rx_port, tx_port):
    transport, protocol = await loop.create_datagram_endpoint(
            lambda: PAM245DatagramProtocol(api),
            ('localhost', rx_port))

    def send_data(data):
        transport.sendto(data, ('localhost', tx_port))

    api.send_data_to_device = send_data

    return transport



