
import random


class Data(object):

    def __init__(self, data):
        self.data = data

    def hex(self):
        return self.data.encode().hex()


class Telemetry(object):
    data = Data('payload')


class ReceivedTelemetry(object):
    telemetry = Telemetry()


class StreamEvent(object):
    def __init__(self):
        self.request_id = random.randint(0, 500000)


class PacketStream(object):

    receive_telemetry_response = ReceivedTelemetry()

    def __init__(self, type='receive_telemetry_response'):
        self._type = type

    def WhichOneof(self, type):
        return self._type


class EventStream(PacketStream):

    def __init__(self, type='stream_event'):
        super().__init__(type=type)
        self.stream_event = StreamEvent()


class MockFraming():
    def Value(self, value):
        return 0


class MockStreamWithEx():
    def OpenSatelliteStream(self, request):
        raise Exception()


class MockStream():
    def OpenSatelliteStream(self, request):
        return [PacketStream(), EventStream()]
