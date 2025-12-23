"""Tests for RPC version functionality in NexDexAccount and NexDex."""

from unittest.mock import MagicMock, patch

from nexdex_py import NexDex
from nexdex_py.account.account import NexDexAccount
from nexdex_py.environment import TESTNET
from tests.mocks.api_client import MockApiClient

TEST_L1_ADDRESS = "0xd2c7314539dCe7752c8120af4eC2AA750Cf2035e"
TEST_L1_PRIVATE_KEY = "0xf8e4d1d772cdd44e5e77615ad11cc071c94e4c06dc21150d903f28e6aa6abdff"
TEST_L2_PRIVATE_KEY = "0x543b6cf6c91817a87174aaea4fb370ac1c694e864d7740d728f8344d53e815"


class TestNexDexAccountRpcVersion:
    """Test RPC version functionality in NexDexAccount."""

    def test_account_without_rpc_version(self):
        """Test that account uses default RPC URL when rpc_version is not provided."""
        api_client = MockApiClient()
        config = api_client.fetch_system_config()

        with patch("nexdex_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            NexDexAccount(
                config=config,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
            )

            # Verify that FullNodeClient was called with the default RPC URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            assert call_args.kwargs["node_url"] == config.starknet_fullnode_rpc_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.NexDex.trade/rpc/v0.5"

    def test_account_with_rpc_version(self):
        """Test that account constructs RPC URL with version when rpc_version is provided."""
        api_client = MockApiClient()
        config = api_client.fetch_system_config()

        with patch("nexdex_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            NexDexAccount(
                config=config,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
                rpc_version="v0_9",
            )

            # Verify that FullNodeClient was called with the constructed URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{config.starknet_fullnode_rpc_base_url}/rpc/v0_9"
            assert call_args.kwargs["node_url"] == expected_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.NexDex.trade/rpc/v0_9"

    def test_account_with_different_rpc_version(self):
        """Test that account works with different RPC versions."""
        api_client = MockApiClient()
        config = api_client.fetch_system_config()

        with patch("nexdex_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            NexDexAccount(
                config=config,
                l1_address=TEST_L1_ADDRESS,
                l2_private_key=TEST_L2_PRIVATE_KEY,
                rpc_version="v0_8",
            )

            # Verify that FullNodeClient was called with the correct version
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{config.starknet_fullnode_rpc_base_url}/rpc/v0_8"
            assert call_args.kwargs["node_url"] == expected_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.NexDex.trade/rpc/v0_8"


class TestNexDexRpcVersion:
    """Test RPC version functionality in NexDex class."""

    def test_NexDex_init_account_with_rpc_version(self):
        """Test that NexDex.init_account passes rpc_version to NexDexAccount."""
        # Create a mock NexDex instance
        NexDex = NexDex.__new__(NexDex)
        NexDex.env = TESTNET
        NexDex.logger = MagicMock()
        NexDex.api_client = MockApiClient()
        NexDex.ws_client = MagicMock()
        NexDex.config = NexDex.api_client.fetch_system_config()
        NexDex.account = None

        with patch("nexdex_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Initialize account with rpc_version
            NexDex.init_account(
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
                rpc_version="v0_9",
            )

            # Verify that FullNodeClient was called with the correct URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{NexDex.config.starknet_fullnode_rpc_base_url}/rpc/v0_9"
            assert call_args.kwargs["node_url"] == expected_url
            assert NexDex.account is not None

    @patch("nexdex_py.NexDex.NexDexApiClient")
    @patch("nexdex_py.NexDex.NexDexWebsocketClient")
    def test_NexDex_init_with_rpc_version(self, mock_ws_client, mock_api_client):
        """Test that NexDex.__init__ passes rpc_version to NexDexAccount."""
        # Setup mocks
        mock_api_instance = MockApiClient()
        mock_api_client.return_value = mock_api_instance
        mock_ws_client.return_value = MagicMock()

        with patch("nexdex_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Create NexDex instance with rpc_version
            NexDex = NexDex(
                env=TESTNET,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
                rpc_version="v0_9",
            )

            # Verify that FullNodeClient was called with the correct URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            expected_url = f"{NexDex.config.starknet_fullnode_rpc_base_url}/rpc/v0_9"
            assert call_args.kwargs["node_url"] == expected_url
            assert NexDex.account is not None

    @patch("nexdex_py.NexDex.NexDexApiClient")
    @patch("nexdex_py.NexDex.NexDexWebsocketClient")
    def test_NexDex_init_without_rpc_version(self, mock_ws_client, mock_api_client):
        """Test that NexDex.__init__ uses default RPC URL when rpc_version is not provided."""
        # Setup mocks
        mock_api_instance = MockApiClient()
        mock_api_client.return_value = mock_api_instance
        mock_ws_client.return_value = MagicMock()

        with patch("nexdex_py.account.account.FullNodeClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            # Create NexDex instance without rpc_version
            NexDex = NexDex(
                env=TESTNET,
                l1_address=TEST_L1_ADDRESS,
                l1_private_key=TEST_L1_PRIVATE_KEY,
            )

            # Verify that FullNodeClient was called with default RPC URL
            mock_client.assert_called_once()
            call_args = mock_client.call_args
            assert call_args.kwargs["node_url"] == NexDex.config.starknet_fullnode_rpc_url
            assert call_args.kwargs["node_url"] == "https://pathfinder.api.testnet.NexDex.trade/rpc/v0.5"
            assert NexDex.account is not None

