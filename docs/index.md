---
hide:
  - navigation
---

# NexDex Python SDK 

!!! warning
    **Experimental SDK, library API is subject to change**

::: NexDex_py.NexDex.NexDex
    handler: python
    options:
      show_source: false
      show_root_heading: true

## L2-Only Authentication (Subkeys)

For users who only have L2 credentials (subkeys) and don't need L1 onboarding:

::: NexDex_py.NexDex_subkey.NexDexSubkey
    handler: python
    options:
      show_source: false
      show_root_heading: true

### Usage Examples

**L1 + L2 Authentication (Traditional):**
```python
from NexDex_py import NexDex
from NexDex_py.environment import Environment

# Requires both L1 and L2 credentials
NexDex = NexDex(
    env=Environment.TESTNET,
    l1_address="0x...",
    l1_private_key="0x..."
)
```

**L2-Only Authentication (Subkeys):**
```python
from NexDex_py import NexDexSubkey
from NexDex_py.environment import Environment

# Only requires L2 credentials - no L1 needed
NexDex = NexDexSubkey(
    env=Environment.TESTNET,
    l2_private_key="0x...",
    l2_address="0x..."
)

# Use exactly like regular NexDex
await NexDex.init_account()  # Already initialized
markets = await NexDex.api_client.get_markets()
```

**WebSocket Usage:**
```python
async def on_message(ws_channel, message):
    print(ws_channel, message)

await NexDex.ws_client.connect()
await NexDex.ws_client.subscribe(NexDexWebsocketChannel.MARKETS_SUMMARY, callback=on_message)
```

### When to Use Each Approach

**Use `NexDex` (L1 + L2) when:**
- You have both L1 (Ethereum) and L2 (Starknet) credentials
- You have never logged in to NexDex using this account before
- You need to perform on-chain operations (transfers, withdrawals)

**Use `NexDexSubkey` (L2-only) when:**
- You only have L2 credentials
- The account has already been onboarded (You have logged in to NexDex before)
- You do not need on-chain operations (withdrawals, transfers)

### Key Differences

| Feature | `NexDex` | `NexDexSubkey` |
|---------|-----------|-----------------|
| **Authentication** | L1 + L2 | L2-only |
| **Onboarding** | ✅ Supported | ❌ Blocked |
| **On-chain Operations** | ✅ Supported | ❌ Blocked |
| **API Access** | ✅ Full access | ✅ Full access |
| **WebSocket** | ✅ Supported | ✅ Supported |
| **Order Management** | ✅ Supported | ✅ Supported |

## API Documentation Links

Full details for REST API & WebSocket JSON-RPC API can be found at the following links:

- [Environment - Testnet](https://docs.api.testnet.NexDex.trade){:target="_blank"}
- [Environment - Prod](https://docs.api.prod.NexDex.trade){:target="_blank"}

::: NexDex_py.api.api_client.NexDexApiClient
    handler: python
    options:
      show_source: false
      show_root_heading: true

::: NexDex_py.api.ws_client.NexDexWebsocketChannel
    handler: python
    options:
      show_source: false
      show_root_heading: true

::: NexDex_py.api.ws_client.NexDexWebsocketClient
    handler: python
    options:
      show_source: false
      show_root_heading: true

::: NexDex_py.account.account.NexDexAccount
    handler: python
    options:
      show_source: false
      show_root_heading: true

::: NexDex_py.account.subkey_account.SubkeyAccount
    handler: python
    options:
      show_source: false
      show_root_heading: true






