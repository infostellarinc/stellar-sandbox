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

"""Unittest of the basic example"""


import unittest
from unittest.mock import patch

from examples import basic
from examples.tests.mock.grpc import MockStreamWithEx, MockFraming


class test_Basic(unittest.TestCase):
    """This class tests the basic example by mocking Infostellar's services"""

    @patch('examples.basic.gauth_jwt')
    @patch('examples.basic.gauth_grpc')
    @patch('examples.basic.stellarstation_pb2')
    @patch('examples.basic.stellarstation_pb2_grpc')
    def test_reconnect(self, mock_pb2_grpc, mock_pb2, mock_grpc, mock_jwt):
        """Basic reconnection test"""

        mock_jwt.Credentials.from_service_account_file.return_value = None
        mock_jwt.OnDemandCredentials.from_signing_credentials.return_value = None
        mock_grpc.secure_authorized_channel.return_value = None
        mock_pb2.Framing = MockFraming()
        mock_pb2_grpc.StellarStationServiceStub.return_value = MockStreamWithEx()
        mock_pb2_grpc.SatelliteStreamRequest.return_value = None

        try:
            satellite = basic.createBitstreamSatelliteChannel(98)
            satellite.logTelemetry(wait=False)
        except Exception:
            self.fail('No exception should have been thrown')
