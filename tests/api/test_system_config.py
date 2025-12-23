from nexdex_py import NexDex
from nexdex_py.environment import TESTNET


def test_system_config():
    NexDex = NexDex(env=TESTNET)
    assert NexDex.config.starknet_gateway_url == "https://potc-testnet-sepolia.starknet.io"
    assert NexDex.config.starknet_chain_id == "PRIVATE_SN_POTC_SEPOLIA"
    assert NexDex.config.block_explorer_url == "https://voyager.testnet.NexDex.trade/"
    assert NexDex.config.bridged_tokens[0].name == "TEST USDC"

