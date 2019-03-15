# Copyright 2018 Infostellar, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC stellarstation-api client."""


import inspect
import logging
import os
from pprint import pformat
import time

from google.auth import jwt as gauth_jwt
from google.auth.transport import grpc as gauth_grpc
from stellarstation.api.v1 import stellarstation_pb2
from stellarstation.api.v1 import stellarstation_pb2_grpc

os.environ['GRPC_SSL_CIPHER_SUITES'] = 'ECDHE-RSA-AES128-GCM-SHA256'


def createBitstreamSatelliteChannel(satellite_id):
    """Factory
    This method creates a satellite channel object that exchanges bitstream
    chunks of data in a bidirectional fashion. Users are responsible for the
    correct serialization / deserialization of the packets through the stream.
    """
    return SatelliteChannel(
        satellite_id, stellarstation_pb2.Framing.Value('BITSTREAM')
    )


def createAnySatelliteChannel(satellite_id):
    """Factory
    This method creates a satellite channel object that exchanges bitstream
    chunks of data in a bidirectional fashion. Users are responsible for the
    correct serialization / deserialization of the packets through the stream.
    """
    return SatelliteChannel(satellite_id, None)


def createIQSatelliteChannel(satellite_id):
    """Factory
    This method creates a satellite channel object that exchanges IQ data in
    between both ends.
    """
    return SatelliteChannel(
        satellite_id, stellarstation_pb2.Framing.Value('IQ')
    )


def createPngSatelliteChannel(satellite_id):
    """Factory
    This method creates a streaming channel that permits receiving the images
    of the decoded data coming from certain weather satellites.
    """
    return SatelliteChannel(
        satellite_id, stellarstation_pb2.Framing.Value('IMAGE_PNG')
    )


class SatelliteChannel(object):
    """
    This class creates a bidirectional communications channel with an existing
    satellite using StellarStation's API.
    """

    def __init__(
        self, satellite_id, framing,
        url='https://api.stellarstation.com',
        channel_url='api.stellarstation.com:443'
    ):
        """Constructor
        Constructs a satellite channel object that connects to the satellite
        identified by the given paramenter. The satellite needs to be
        registered within StellarStation's platform and accessible to the user
        whose credentials are used for the connection. For a given user, the
        satellites that can be accessed through the API are listed in the
        console.

        @param satellite_id -- identifier of the satellite to connect to
        @param framing -- identifier that defines the protocol running on top
        @param url -- URL of StellarStation's API
        @param channel_url -- service definition for DNS resolution
        """
        self._l = logging.getLogger(self.__class__.__name__)
        self._l.setLevel(logging.DEBUG)

        # ch = logging.StreamHandler()
        # ch.setLevel(logging.DEBUG)
        # ch.setFormatter(logging.Formatter(
        #    "%(asctime)s|%(levelname)s|%(message)s", "%Y-%m-%d %H:%M:%S"
        # ))
        # self._l.addHandler(ch)

        self.satellite_id = satellite_id
        self.framing = framing

        self._l.info('framing = %s', framing)
        self._l.info('framing = %s', self.framing)

        if self.framing:
            self._protocol_name = stellarstation_pb2.Framing.Name(self.framing)
        else:
            self._protocol_name = 'None'

        self._url = url
        self._channel_url = channel_url

        self._createSecureChannel()

    def _createSecureChannel(self):
        """
        This method creates a client for StellarStation's API.
        """
        home = os.path.expanduser('~')
        key = os.path.join(
            # home, '.infostellar/stellarstation-private-key.json'
            home, '.infostellar/demo-private-key.json'
        )

        credentials = gauth_jwt.Credentials.from_service_account_file(
            key, audience=self._url
        )
        jwt_creds = gauth_jwt.OnDemandCredentials.from_signing_credentials(
            credentials
        )
        self.channel = gauth_grpc.secure_authorized_channel(
            jwt_creds, None, self._channel_url
        )

        self.client = stellarstation_pb2_grpc.StellarStationServiceStub(
            self.channel
        )

        self._l.info(
            'Connected to (%s), satellite = %s, protocol = %s',
            self._url, self.satellite_id, self._protocol_name
        )

    def _createRequest(self):
        """
        This method creates a request for the satellite stream.
        """
        if self.framing is None:
            self._l.info('Satellite stream, framing ANY')
            yield stellarstation_pb2.SatelliteStreamRequest(
                satellite_id=str(self.satellite_id)
            )
        else:
            self._l.info('Satellite stream, framing = %s', self.framing)
            yield stellarstation_pb2.SatelliteStreamRequest(
                satellite_id=str(self.satellite_id),
                accepted_framing=[self.framing]
            )

        while True:
            self._l.debug('.')
            time.sleep(3000)

    def getStream(self):
        """
        This method returns a data stream for satellite telemetry read.
        """
        self.request = self._createRequest()
        self._l.info('request = %s' % self.request)
        self.stream = self.client.OpenSatelliteStream(self.request)

    def logTelemetry(self, wait=True, retryTime=5):
        """
        This method leaves the client listening for data coming from the
        satellite through the open stream. The data is logged into the default
        logging service from the Python library.

        # notice # This is an example of how to use this class for waiting for
                    frames.
        # notice # For connecting with an external service, it is recommended
                    to retrieve the stream through "getStream()" and to iterate
                    over it like it is done in this function.
        """
        self.getStream()

        while wait:

            try:
                self._l.debug('Waiting for frames to arrive...')

                for response in self.stream:
                    type = response.WhichOneof("Response")

                    if type == 'receive_telemetry_response':
                        self._l.info(
                            'response::telemetry = <%s>',
                            response.receive_telemetry_response.telemetry.data
                        )
                        continue

                    if type == 'stream_event':
                        self._l.debug(
                            'stream event::request_id <%s>',
                            response.stream_event.request_id
                        )
                        continue

            except Exception as ex:
                self._l.warn('Exception while waiting for TM, msg = %s', ex)

            time.sleep(retryTime)

    def printServices(self):
        """
        This method logs the available API services (methods / classes).
        """
        self._services = {c[0]: c[1] for c in inspect.getmembers(
            stellarstation_pb2, predicate=inspect.isclass
        )}

        self._gprcServices = [
            m for m in dir(self.client)
            if callable(getattr(self.client, m)) and not m.startswith('__')
        ]

        self._l.info('Callable items within the API:')
        self._l.info('API available classes = \n%s', pformat(self._services))
        self._l.info('GRPC methods = \n%s', pformat(self._gprcServices))

    def sendTelecommand(self, tcArray):
        """
        This method sends an array of telecommands through the open stream.

        @param tcArray -- array of telecommands to be sent, each of them needs
                            to be a bytearray object
        """
        self._l.debug('Telecommands array request')

        command_request = stellarstation_pb2.SendSatelliteCommandsRequest(
            output_framing=self.framing, command=tcArray
        )
        satellite_stream_request = stellarstation_pb2.SatelliteStreamRequest(
            satellite_id=self.satellite_id,
            send_satellite_commands_request=command_request
        )

        yield satellite_stream_request
        self._l.debug('Telecommands array sent')


if __name__ == '__main__':

    # 61 is an example of an identifier for a satellite.
    # The class provided in this example is suppossed to be used like this:
    # satellite = createAnySatelliteChannel(98)
    satellite = createBitstreamSatelliteChannel(98)
    # createBitstreamSatelliteChannel # use this for decoded packets

    # The following method can be called to print the available classes and
    # methods in the API.
    # satellite.printServices()

    # The following method can be used to send telecommands to the satellite
    # satellite.sendTelecommand([b'05050505'])

    # The following method waits for telemetry frames and logs their content.
    satellite.logTelemetry()
