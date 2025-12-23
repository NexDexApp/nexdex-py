import json
import logging
import time
import types
from decimal import Decimal
from enum import IntEnum
 
from httpx import AsyncClient
from starknet_py.common import int_from_bytes, int_from_hex
from starknet_py.hash.address import compute_address
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.http_client import HttpMethod
from starknet_py.net.signer.stark_curve_signer import KeyPair

from nexdex_py.account.starknet import Account as StarknetAccount
from nexdex_py.account.utils import derive_stark_key, derive_stark_key_from_ledger, flatten_signature
from nexdex_py.api.models import SystemConfig
from nexdex_py.common.order import Order
from nexdex_py.message.auth import build_auth_message, build_fullnode_message
from nexdex_py.message.block_trades import BlockTrade, build_block_trade_message
from nexdex_py.message.onboarding import build_onboarding_message
from nexdex_py.message.order import build_modify_order_message, build_order_message
from nexdex_py.message.stark_key import build_stark_key_message
from nexdex_py.utils import raise_value_error

FULLNODE_SIGNATURE_VERSION = "1.0.0"


# For matching existing chainId type
class CustomStarknetChainId(IntEnum):
    PRIVATE_SN_MAINNET = int_from_bytes(b"PRIVATE_SN_PARACLEAR_MAINNET")
    PRIVATE_SN_TESTNET_MOCK_SEPOLIA = int_from_bytes(b"PRIVATE_SN_POTC_MOCK_SEPOLIA")
    PRIVATE_SN_TESTNET_SEPOLIA = int_from_bytes(b"PRIVATE_SN_POTC_SEPOLIA")


class NexDexAccount:
    """Class to generate and manage NexDex account.
        Initialized along with `NexDex` class.

    Args:
        config (SystemConfig): SystemConfig
        l1_address (str): Ethereum address
        l1_private_key (Optional[str], optional): Ethereum private key. Defaults to None.
        l2_private_key (Optional[str], optional): NexDex private key. Defaults to None.
        rpc_version (Optional[str], optional): RPC version (e.g., "v0_9"). If provided, constructs URL as {base_url}/rpc/{rpc_version}. Defaults to None.

    Examples:
        >>> from nexdex_py import NexDex
        >>> from nexdex_py.environment import Environment
        >>> NexDex = NexDex(env=Environment.TESTNET, l1_address="0x...", l1_private_key="0x...")
        >>> NexDex.account.l2_address
        >>> NexDex.account.l2_public_key
        >>> NexDex.account.l2_private_key
    """

    def __init__(
        self,
        config: SystemConfig,
        l1_address: str,
        l1_private_key_from_ledger: bool | None = False,
        l1_private_key: str | None = None,
        l2_private_key: str | None = None,
        rpc_version: str | None = None,
    ):
        self.config = config

        if l1_address is None:
            return raise_value_error("NexDex: Provide Ethereum address")
        self.l1_address = l1_address

        if l1_private_key is not None:
            self.l1_private_key = int_from_hex(l1_private_key)
            stark_key_msg = build_stark_key_message(int(config.l1_chain_id))
            self.l2_private_key = derive_stark_key(self.l1_private_key, stark_key_msg)
        elif l1_private_key_from_ledger:
            stark_key_msg = build_stark_key_message(int(config.l1_chain_id))
            self.l2_private_key = derive_stark_key_from_ledger(l1_address, stark_key_msg)
        elif l2_private_key is not None:
            self.l2_private_key = int_from_hex(l2_private_key)
        else:
            return raise_value_error("NexDex: Provide Ethereum or NexDex private key")

        key_pair = KeyPair.from_private_key(self.l2_private_key)
        self.l2_public_key = key_pair.public_key
        self.l2_address = self._account_address()

        # Create starknet account
        if rpc_version:
            node_url = f"{config.starknet_fullnode_rpc_base_url}/rpc/{rpc_version}"
        else:
            node_url = config.starknet_fullnode_rpc_url
        client = FullNodeClient(node_url=node_url)
        self.l2_chain_id = int_from_bytes(config.starknet_chain_id.encode())
        self.starknet = StarknetAccount(
            client=client,
            address=self.l2_address,
            key_pair=key_pair,
            chain=CustomStarknetChainId(self.l2_chain_id),  # type: ignore[arg-type]
        )

        # Apply the fullnode headers patch
        self._apply_fullnode_headers_patch(client)

    # Monkey patch of _make_request method of starknet.py client
    # to inject http headers requested by NexDex full node:
    # - NexDex-STARKNET-ACCOUNT: account address signing the request
    # - NexDex-STARKNET-SIGNATURE: signature of the request
    # - NexDex-STARKNET-SIGNATURE-TIMESTAMP: timestamp of the signature
    # - NexDex-STARKNET-SIGNATURE-VERSION: version of the signature
    def _apply_fullnode_headers_patch(self, client):
        """Apply the fullnode headers patch for NexDex-specific headers."""
        current_self = self

        async def monkey_patched_make_request(
            self,
            session: AsyncClient,
            address: str,
            http_method: HttpMethod,
            params: dict,
            payload: dict,
        ) -> dict:
            json_payload = json.dumps(payload)
            headers = current_self.fullnode_request_headers(
                current_self.starknet, current_self.l2_chain_id, json_payload
            )

            response = await session.request(
                method=http_method.value, url=address, params=params, json=payload, headers=headers
            )
            await self.handle_request_error(response)
            return await response.json()

        client._client._make_request = types.MethodType(monkey_patched_make_request, client._client)

    def _account_address(self) -> int:
        calldata = [
            int_from_hex(self.config.paraclear_account_hash),
            get_selector_from_name("initialize"),
            2,
            self.l2_public_key,
            0,
        ]

        address = compute_address(
            class_hash=int_from_hex(self.config.paraclear_account_proxy_hash),
            constructor_calldata=calldata,
            salt=self.l2_public_key,
        )
        return address

    def set_jwt_token(self, jwt_token: str) -> None:
        self.jwt_token = jwt_token

    def onboarding_signature(self) -> str:
        if self.config is None:
            return raise_value_error("NexDex: System config not loaded")
        message = build_onboarding_message(self.l2_chain_id)
        sig = self.starknet.sign_message(message)
        return flatten_signature(sig)

    def onboarding_headers(self) -> dict:
        return {
            "NexDex-ETHEREUM-ACCOUNT": self.l1_address,
            "NexDex-STARKNET-ACCOUNT": hex(self.l2_address),
            "NexDex-STARKNET-SIGNATURE": self.onboarding_signature(),
        }

    def auth_signature(self, timestamp: int, expiry: int) -> str:
        message = build_auth_message(self.l2_chain_id, timestamp, expiry)
        sig = self.starknet.sign_message(message)
        return flatten_signature(sig)

    def auth_headers(self) -> dict:
        timestamp = int(time.time())
        expiry = timestamp + 24 * 60 * 60
        return {
            "NexDex-STARKNET-ACCOUNT": hex(self.l2_address),
            "NexDex-STARKNET-SIGNATURE": self.auth_signature(timestamp, expiry),
            "NexDex-TIMESTAMP": str(timestamp),
            "NexDex-SIGNATURE-EXPIRATION": str(expiry),
        }

    def fullnode_request_headers(self, account: StarknetAccount, chain_id: int, json_payload: str):
        signature_timestamp = int(time.time())
        account_address = hex(account.address)
        message = build_fullnode_message(
            chain_id,
            account_address,
            json_payload,
            signature_timestamp,
            FULLNODE_SIGNATURE_VERSION,
        )
        sig = account.sign_message(message)
        return {
            "Content-Type": "application/json",
            "NexDex-STARKNET-ACCOUNT": account_address,
            "NexDex-STARKNET-SIGNATURE": f'["{sig[0]}","{sig[1]}"]',
            "NexDex-STARKNET-SIGNATURE-TIMESTAMP": str(signature_timestamp),
            "NexDex-STARKNET-SIGNATURE-VERSION": FULLNODE_SIGNATURE_VERSION,
        }

    def sign_order(self, order: Order) -> str:
        if order.id:
            sig = self.starknet.sign_message(build_modify_order_message(self.l2_chain_id, order))
        else:
            sig = self.starknet.sign_message(build_order_message(self.l2_chain_id, order))
        return flatten_signature(sig)

    def sign_block_trade(self, block_trade_data: BlockTrade) -> str:
        """Sign block trade data using Starknet account.
        Args:
            block_trade_data (dict): Block trade data containing trade details
        Returns:
            dict: Signed block trade data
        """
        # Convert block trade data to TypedData format
        typed_data = build_block_trade_message(self.l2_chain_id, block_trade_data)
        sig = self.starknet.sign_message(typed_data)
        return flatten_signature(sig)

    def sign_block_offer(self, offer_data: BlockTrade) -> str:
        """Sign block offer data using Starknet account.
        Args:
            offer_data (dict): Block offer data containing offer details
        Returns:
            dict: Signed block offer data
        """
        # Convert block offer data to TypedData format
        typed_data = build_block_trade_message(self.l2_chain_id, offer_data)
        sig = self.starknet.sign_message(typed_data)
        return flatten_signature(sig)

    async def transfer_on_l2(self, target_l2_address: str, amount_decimal: Decimal):
        try:
            # Load contracts
            paraclear_address = int_from_hex(self.config.paraclear_address)
            usdc_address = int_from_hex(self.config.bridged_tokens[0].l2_token_address)
            paraclear_contract = await self.starknet.load_contract(paraclear_address, is_cairo0_contract=False)
            account_contract = await self.starknet.load_contract(self.l2_address, is_cairo0_contract=True)

            paraclear_decimals = self.config.paraclear_decimals

            # Get token asset balance
            token_asset_balance = await paraclear_contract.functions["getTokenAssetBalance"].call(
                account=self.l2_address, token_address=usdc_address
            )
            logging.info(f"USDC balance on Paraclear: {token_asset_balance[0] / 10**paraclear_decimals}")

            # Calculate amounts
            amount_paraclear = int(amount_decimal * 10**paraclear_decimals)
            logging.info(f"Amount to transfer to {target_l2_address}: {amount_paraclear}")

            # Prepare calls
            calls = [
                paraclear_contract.functions["transfer"].prepare_invoke_v3(
                    recipient=int_from_hex(target_l2_address),
                    token_address=usdc_address,
                    amount=amount_paraclear,
                ),
            ]

            # Check if multisig is required
            need_multisig = await self.starknet.check_multisig_required(account_contract)

            # Prepare and send transaction
            func_name = "transferOnL2"
            prepared_invoke = await self.starknet.prepare_invoke(calls=calls)
            await self.starknet.process_invoke(account_contract, need_multisig, prepared_invoke, func_name)

        except Exception as e:
            logging.exception(f"Error during transfer_on_l2: {e}")
            # Re-raise the exception to handle it upstream if necessary
            raise

