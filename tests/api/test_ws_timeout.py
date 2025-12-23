"""Simple WebSocket timeout tests that don't hang."""

from nexdex_py import NexDex
from nexdex_py.api.ws_client import NexDexWebsocketClient
from nexdex_py.constants import WS_TIMEOUT
from nexdex_py.environment import TESTNET

MOCK_L1_PRIVATE_KEY = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
MOCK_L1_ADDRESS = "0xabcdef0123456789abcdef0123456789abcdef01"


class TestWebSocketTimeout:
    """Simple test suite for WebSocket timeout configuration functionality."""

    def test_default_timeout_from_constant(self):
        """Test that WebSocket client uses default timeout from constants."""
        ws_client = NexDexWebsocketClient(env=TESTNET, auto_start_reader=False)
        assert ws_client.ws_timeout == WS_TIMEOUT
        assert ws_client.ws_timeout == 20  # Current default value

    def test_custom_timeout_parameter(self):
        """Test that custom timeout parameter is properly set."""
        custom_timeout = 2
        ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=custom_timeout, auto_start_reader=False)
        assert ws_client.ws_timeout == custom_timeout

    def test_none_timeout_uses_default(self):
        """Test that passing None for timeout uses the default."""
        ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=None, auto_start_reader=False)
        assert ws_client.ws_timeout == WS_TIMEOUT

    def test_timeout_parameter_types(self):
        """Test that timeout parameter accepts different integer values."""
        test_values = [1, 2, 3, 5, 10]
        for timeout_value in test_values:
            ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=timeout_value, auto_start_reader=False)
            assert ws_client.ws_timeout == timeout_value

    def test_NexDex_class_timeout_passthrough_default(self):
        """Test that NexDex class properly creates WebSocket client with default timeout."""
        NexDex = NexDex(env=TESTNET)
        assert NexDex.ws_client.ws_timeout == WS_TIMEOUT

    def test_NexDex_class_timeout_passthrough_custom(self):
        """Test that NexDex class properly passes custom timeout to WebSocket client."""
        custom_timeout = 3
        NexDex = NexDex(env=TESTNET, ws_timeout=custom_timeout)
        assert NexDex.ws_client.ws_timeout == custom_timeout

    def test_NexDex_class_timeout_none_uses_default(self):
        """Test that passing None for timeout uses the default."""
        NexDex = NexDex(env=TESTNET, ws_timeout=None)
        assert NexDex.ws_client.ws_timeout == WS_TIMEOUT

    def test_timeout_edge_cases(self):
        """Test edge cases for timeout values."""
        # Test minimum reasonable values
        ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=1)
        assert ws_client.ws_timeout == 1

        # Test zero (though not recommended in practice)
        ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=0)
        assert ws_client.ws_timeout == 0

        # Test larger values
        ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=10)
        assert ws_client.ws_timeout == 10

    def test_timeout_with_account_initialization(self):
        """Test that timeout setting persists through account initialization."""
        custom_timeout = 2
        NexDex = NexDex(
            env=TESTNET, l1_address=MOCK_L1_ADDRESS, l1_private_key=MOCK_L1_PRIVATE_KEY, ws_timeout=custom_timeout
        )

        # Ensure timeout is preserved after account initialization
        assert NexDex.ws_client.ws_timeout == custom_timeout
        assert NexDex.account is not None  # Account should be initialized

    def test_timeout_parameter_independence(self):
        """Test that different WebSocket clients can have different timeouts."""
        timeout1 = 1
        timeout2 = 3

        ws_client1 = NexDexWebsocketClient(env=TESTNET, ws_timeout=timeout1)
        ws_client2 = NexDexWebsocketClient(env=TESTNET, ws_timeout=timeout2)

        assert ws_client1.ws_timeout == timeout1
        assert ws_client2.ws_timeout == timeout2
        assert ws_client1.ws_timeout != ws_client2.ws_timeout

    def test_backward_compatibility(self):
        """Test that existing code without timeout parameter still works."""
        # This should work exactly as before
        ws_client = NexDexWebsocketClient(env=TESTNET, auto_start_reader=False)
        assert ws_client.ws_timeout == WS_TIMEOUT

        # NexDex class without timeout should also work
        NexDex = NexDex(env=TESTNET)
        assert NexDex.ws_client.ws_timeout == WS_TIMEOUT

    def test_integration_with_existing_features(self):
        """Test that timeout configuration works with other WebSocket client features."""
        custom_timeout = 2
        ws_client = NexDexWebsocketClient(env=TESTNET, ws_timeout=custom_timeout, auto_start_reader=False)

        # Test that other properties are still properly initialized
        assert ws_client.env == TESTNET
        assert ws_client.callbacks == {}
        assert ws_client.subscribed_channels == {}
        assert ws_client.ws_timeout == custom_timeout
        assert ws_client.api_url == f"wss://ws.api.{TESTNET}.NexDex.trade/v1"

    def test_timeout_parameter_in_constructor(self):
        """Test that timeout parameter is properly handled in constructor."""
        # Test with explicit None
        ws_client1 = NexDexWebsocketClient(env=TESTNET, ws_timeout=None)
        assert ws_client1.ws_timeout == WS_TIMEOUT

        # Test with custom value
        ws_client2 = NexDexWebsocketClient(env=TESTNET, ws_timeout=5)
        assert ws_client2.ws_timeout == 5

        # Test with zero
        ws_client3 = NexDexWebsocketClient(env=TESTNET, ws_timeout=0)
        assert ws_client3.ws_timeout == 0

