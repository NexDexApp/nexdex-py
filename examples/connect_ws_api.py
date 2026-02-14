import asyncio
import os

from starknet_py.common import int_from_hex

from nexdex_py import NexDex
from nexdex_py.api.ws_client import NexDexWebsocketChannel
from nexdex_py.environment import TESTNET  

# Environment variables  
TEST_L1_ADDRESS = os.getenv("L1_ADDRESS", "")
TEST_L1_PRIVATE_KEY = int_from_hex(os.getenv("L1_PRIVATE_KEY", ""))
LOG_FILE = os.getenv("LOG_FILE", "FALSE").lower() == "true"


if LOG_FILE:
    from nexdex_py.common.file_logging import file_logger

    logger = file_logger
    logger.info("Using file logger")
else:
    from nexdex_py.common.console_logging import console_logger

    logger = console_logger
    logger.info("Using console logger")


async def callback_general(ws_channel: NexDexWebsocketChannel, message: dict) -> None:
    message.get("params", {}).get("channel")
    market = message.get("params", {}).get("data", {}).get("market")
    logger.info(f"callback_general(): Channel:{ws_channel} market:{market} message:{message}")


async def NexDex_ws_subscribe(NexDex: NexDex) -> None:
    """This function subscribes to all Websocket channels
    For market specific channels subscribe to ETH-USD-PERP market"""
    is_connected = False
    while not is_connected:
        is_connected = await NexDex.ws_client.connect()
        if not is_connected:
            logger.info("connection failed, retrying in 1 second")
            await asyncio.sleep(1)
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.ACCOUNT,
        callback_general,
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.BALANCE_EVENTS,
        callback_general,
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.BBO,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.FILLS,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.FUNDING_DATA,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.FUNDING_PAYMENTS,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.FUNDING_RATE_COMPARISON,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.MARKETS_SUMMARY,
        callback=callback_general,
        params={"market": "BTC-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.ORDERS,
        callback=callback_general,
        params={"market": "ALL"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.ORDER_BOOK,
        callback=callback_general,
        params={"market": "ETH-USD-PERP", "refresh_rate": "100ms", "price_tick": "0_1", "depth": 15},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.POSITIONS,
        callback_general,
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.TRADES,
        callback=callback_general,
        params={"market": "ETH-USD-PERP"},
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.TRADEBUSTS,
        callback_general,
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.TRANSACTIONS,
        callback_general,
    )
    await NexDex.ws_client.subscribe(
        NexDexWebsocketChannel.TRANSFERS,
        callback_general,
    )


NexDex = NexDex(
    env=TESTNET,
    l1_address=TEST_L1_ADDRESS,
    l1_private_key=TEST_L1_PRIVATE_KEY,
    logger=logger,
)

asyncio.get_event_loop().run_until_complete(NexDex_ws_subscribe(NexDex))
asyncio.get_event_loop().run_forever()


