"""The Hello, state! integration."""
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class PAM245Api:

    def __init__(self, serial_port: str) -> None:
        self.serial_port = serial_port
        self.volume = 0
        self.firmware_version = "0.0.todo"
        self.name = f"MyPAM245 ({serial_port})"
        self.available = True
        self._callbacks = set()
        self._unparsed = ''
        print(f"Hello PAM245Api! ({serial_port})")
        _LOGGER.info(f"Log PAM245Api! ({serial_port})")

    async def set_volume(self, volume: int) -> None:
        if 0 <= volume <= 79:
            self.volume = volume
            _LOGGER.info(f"Set volume to {volume}")
            self._send_command(f"Volume {volume}")
        else:
            _LOGGER.warning(f"Commanded volume out of range ({volume})")

    def add_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.discard(callback)

    def _process_events_from_device(self, events):
        for event_type, *event_data in events:
            match event_type:
                case 'Volume':
                    (volume_string,) = event_data
                    volume = int(volume_string)
                    self._event_volume(volume)
                case _:
                    unknown_event = ' '.join((event_type, *event_data))
                    _LOGGER.warning(f'Unknown event: {unknown_event}')

    def _event_volume(self, volume):
        if 0 <= volume <= 79:
            self.volume = volume
            self._call_callbacks()
        else:
            _LOGGER.warning(f"Event volume out of range ({volume})")

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


async def start_serial_connection(loop, api):
    transport, protocol = await pyserial_asyncio.create_serial_connection(
            loop,
            lambda: PAM245SerialProtocol(api),
            api.serial_port)

    def send_data(data):
        transport.write(data)

    api.send_data_to_device = send_data

    return transport


async def start_datagram_connection(loop, api):
    RX_PORT = 22222
    TX_PORT = 33333

    transport, protocol = await loop.create_datagram_endpoint(
            lambda: PAM245DatagramProtocol(api),
            ('localhost', RX_PORT))

    def send_data(data):
        transport.sendto(data, ('localhost', TX_PORT))

    api.send_data_to_device = send_data

    return transport



