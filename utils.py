"""
Utility functions for the MAITRIX bot.
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from dotenv import load_dotenv

from config import (
    TOKEN_ADDRESSES,
    TOKEN_ABI,
    EXPLORER_URL,
    GAS_PRICE_GWEI,
    GAS_LIMIT,
    TX_CONFIRMATIONS,
    TX_TIMEOUT,
    RPC_URL,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def load_env() -> Dict[str, str]:
    """Load environment variables from .env file."""
    load_dotenv()

    required_vars = ["PRIVATE_KEY"]
    env_vars = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"Missing required environment variable: {var}")
        env_vars[var] = value

    # Add RPC URL from config
    env_vars["RPC_URL"] = RPC_URL

    return env_vars

def setup_web3(rpc_url: str = None) -> Tuple[Web3, Account]:
    """Set up Web3 connection and account."""
    if rpc_url is None:
        rpc_url = RPC_URL

    web3 = Web3(Web3.HTTPProvider(rpc_url))

    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to RPC URL: {rpc_url}")

    # Load private key and create account
    load_dotenv()
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise ValueError("Private key not found in environment variables")

    # Add 0x prefix if not present
    if not private_key.startswith("0x"):
        private_key = f"0x{private_key}"

    account = Account.from_key(private_key)
    logger.info(f"Connected to network. Account: {account.address}")

    return web3, account

def get_token_contract(web3: Web3, token_symbol: str, abi: list = None) -> Any:
    """Get token contract instance."""
    if token_symbol not in TOKEN_ADDRESSES:
        raise ValueError(f"Unknown token symbol: {token_symbol}")

    token_address = TOKEN_ADDRESSES[token_symbol]
    contract_abi = abi if abi else TOKEN_ABI

    return web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=contract_abi)

def get_token_balance(web3: Web3, token_contract: Any, address: str) -> Tuple[int, int, str]:
    """Get token balance, decimals, and symbol."""
    balance = token_contract.functions.balanceOf(address).call()
    decimals = token_contract.functions.decimals().call()
    symbol = token_contract.functions.symbol().call()

    return balance, decimals, symbol

def format_amount(amount: int, decimals: int) -> str:
    """Format token amount with proper decimal places."""
    return str(Decimal(amount) / Decimal(10 ** decimals))

def wait_for_transaction(web3: Web3, tx_hash: str, confirmations: int = 1) -> Dict[str, Any]:
    """Wait for transaction to be confirmed."""
    start_time = time.time()

    while True:
        if time.time() - start_time > TX_TIMEOUT:
            raise TimeoutError(f"Transaction {tx_hash.hex()} timed out after {TX_TIMEOUT} seconds")

        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt is None:
                time.sleep(2)
                continue

            if receipt["status"] == 0:
                raise ValueError(f"Transaction {tx_hash.hex()} failed")

            current_block = web3.eth.block_number
            if current_block - receipt["blockNumber"] >= confirmations:
                logger.info(f"Transaction confirmed: {EXPLORER_URL}{tx_hash.hex()}")
                return receipt

            logger.info(f"Waiting for {confirmations} confirmations... "
                       f"({current_block - receipt['blockNumber']}/{confirmations})")
            time.sleep(5)

        except TransactionNotFound:
            logger.info(f"Transaction {tx_hash.hex()} not found yet. Waiting...")
            time.sleep(5)

def build_tx_params(web3: Web3, from_address: str, to_address: str,
                   gas_price_gwei: float = None, gas_limit: int = None, data: str = None, value: int = 0) -> Dict[str, Any]:
    """Build transaction parameters."""
    if gas_price_gwei is None:
        gas_price_gwei = GAS_PRICE_GWEI

    if gas_limit is None:
        gas_limit = GAS_LIMIT

    gas_price = web3.to_wei(gas_price_gwei, "gwei")

    tx_params = {
        "from": from_address,
        "to": to_address,
        "gasPrice": gas_price,
        "gas": gas_limit,
        "nonce": web3.eth.get_transaction_count(from_address),
        "value": value,
    }

    if data:
        tx_params["data"] = data

    return tx_params

def send_transaction(web3: Web3, account: Account, tx_params: Dict[str, Any],
                    confirmations: int = None) -> Dict[str, Any]:
    """Sign and send transaction."""
    if confirmations is None:
        confirmations = TX_CONFIRMATIONS

    signed_tx = account.sign_transaction(tx_params)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    logger.info(f"Transaction sent: {EXPLORER_URL}{tx_hash.hex()}")

    return wait_for_transaction(web3, tx_hash, confirmations)
