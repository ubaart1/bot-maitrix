"""
Main bot logic for the MAITRIX bot.
"""

import time
import logging
from typing import Dict, Any, List, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account import Account

from config import (
    TOKEN_ADDRESSES,
    FAUCET_ADDRESSES,
    STAKING_ADDRESSES,
    SWAP_ADDRESSES,
    SWAP_PAIRS,
    MIN_BALANCE,
    SWAP_PERCENTAGE,
    STAKE_PERCENTAGE,
    TOKEN_ABI,
    MINT_TOKEN_ABI,
    STAKE_TOKEN_ABI,
    SWAP_ATH_ABI,
    SWAP_VANA_ABI,
)
from utils import (
    get_token_contract,
    get_token_balance,
    format_amount,
    build_tx_params,
    send_transaction,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

class MaitrixBot:
    """Bot for automating mint → swap → stake operations on MAITRIX testnet."""

    def __init__(self, web3: Web3, account: Account):
        """Initialize the bot with Web3 connection and account."""
        self.web3 = web3
        self.account = account
        self.address = account.address

        # Initialize token contracts
        self.token_contracts = {}
        for symbol in TOKEN_ADDRESSES:
            self.token_contracts[symbol] = get_token_contract(web3, symbol, TOKEN_ABI)

        # Initialize token balances
        self.token_balances = {}
        self.update_all_balances()

        logger.info(f"MaitrixBot initialized for address: {self.address}")

    def update_all_balances(self) -> None:
        """Update balances for all tokens."""
        for symbol, contract in self.token_contracts.items():
            balance, decimals, _ = get_token_balance(self.web3, contract, self.address)
            self.token_balances[symbol] = {
                "balance": balance,
                "decimals": decimals,
                "formatted": format_amount(balance, decimals)
            }
            logger.info(f"Balance of {symbol}: {self.token_balances[symbol]['formatted']}")

    def approve_token(self, token_symbol: str, spender_address: str, amount: int) -> Dict[str, Any]:
        """Approve token spending."""
        token_contract = self.token_contracts[token_symbol]

        # Check if approval is needed
        current_allowance = token_contract.functions.allowance(
            self.address, spender_address
        ).call()

        if current_allowance >= amount:
            logger.info(f"Approval not needed for {token_symbol}. Current allowance: {current_allowance}")
            return None

        logger.info(f"Approving {format_amount(amount, self.token_balances[token_symbol]['decimals'])} "
                   f"{token_symbol} for spender {spender_address}")

        tx_data = token_contract.functions.approve(
            spender_address, amount
        ).build_transaction({
            "from": self.address,
            "nonce": self.web3.eth.get_transaction_count(self.address),
        })

        return send_transaction(self.web3, self.account, tx_data)

    def mint_token(self, token_symbol: str, amount: int) -> Dict[str, Any]:
        """Mint tokens if possible."""
        if token_symbol not in TOKEN_ADDRESSES:
            logger.warning(f"Unknown token symbol: {token_symbol}")
            return None

        # Get contract with mint ABI
        token_address = TOKEN_ADDRESSES[token_symbol]
        token_contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=MINT_TOKEN_ABI
        )

        try:
            # Check if contract has mint function
            token_contract.functions.mint
        except AttributeError:
            logger.warning(f"Token {token_symbol} does not have a mint function")
            return None

        logger.info(f"Minting {format_amount(amount, self.token_balances[token_symbol]['decimals'])} "
                   f"{token_symbol}")

        tx_data = token_contract.functions.mint(amount).build_transaction({
            "from": self.address,
            "nonce": self.web3.eth.get_transaction_count(self.address),
        })

        return send_transaction(self.web3, self.account, tx_data)

    def swap_token(self, from_token: str, to_token: str, amount: int) -> Dict[str, Any]:
        """Swap tokens."""
        swap_key = f"{from_token}_TO_{to_token}"

        if swap_key not in SWAP_ADDRESSES:
            logger.warning(f"No swap router found for {from_token} to {to_token}")
            return None

        router_address = SWAP_ADDRESSES[swap_key]

        # Approve token for swap
        self.approve_token(from_token, router_address, amount)

        # Get router contract with appropriate ABI based on token pair
        abi = None
        function_name = None

        if from_token == "ATH" and to_token == "AUSD":
            abi = SWAP_ATH_ABI
            function_name = "swapATHtoAUSD"
        elif from_token == "VANA" and to_token == "VANAUSD":
            abi = SWAP_VANA_ABI
            function_name = "swapVANAtoVANAUSD"
        else:
            # Default ABI for other pairs
            abi = [
                {
                    "name": "mint",
                    "type": "function",
                    "inputs": [{"name": "amount", "type": "uint256"}],
                    "outputs": []
                }
            ]
            function_name = "mint"

        router_contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(router_address),
            abi=abi
        )

        logger.info(f"Swapping {format_amount(amount, self.token_balances[from_token]['decimals'])} "
                   f"{from_token} to {to_token}")

        # Call the appropriate function based on token pair
        function = getattr(router_contract.functions, function_name)
        tx_data = function(amount).build_transaction({
            "from": self.address,
            "nonce": self.web3.eth.get_transaction_count(self.address),
        })

        return send_transaction(self.web3, self.account, tx_data)

    def stake_token(self, token_symbol: str, amount: int) -> Dict[str, Any]:
        """Stake tokens."""
        if token_symbol not in STAKING_ADDRESSES:
            logger.warning(f"No staking pool found for {token_symbol}")
            return None

        staking_address = STAKING_ADDRESSES[token_symbol]

        # Approve token for staking
        self.approve_token(token_symbol, staking_address, amount)

        # Get staking contract
        staking_contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(staking_address),
            abi=STAKE_TOKEN_ABI
        )

        logger.info(f"Staking {format_amount(amount, self.token_balances[token_symbol]['decimals'])} "
                   f"{token_symbol}")

        tx_data = staking_contract.functions.stake(amount).build_transaction({
            "from": self.address,
            "nonce": self.web3.eth.get_transaction_count(self.address),
        })

        return send_transaction(self.web3, self.account, tx_data)

    def run_auto_cycle(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run the full mint → swap → stake cycle automatically."""
        results = {
            "mint": [],
            "swap": [],
            "stake": []
        }

        # Update balances
        self.update_all_balances()

        # 1. Mint tokens if balance is low
        for token_symbol in TOKEN_ADDRESSES:
            balance = self.token_balances[token_symbol]["balance"]
            min_balance = MIN_BALANCE.get(token_symbol, 0)

            if balance < min_balance:
                mint_amount = min_balance * 2  # Mint double the minimum balance
                mint_result = self.mint_token(token_symbol, mint_amount)

                if mint_result:
                    results["mint"].append({
                        "token": token_symbol,
                        "amount": mint_amount,
                        "tx_hash": mint_result["transactionHash"].hex()
                    })

        # Update balances after minting
        self.update_all_balances()

        # 2. Swap tokens
        for from_token, to_token in SWAP_PAIRS.items():
            balance = self.token_balances[from_token]["balance"]

            if balance > 0:
                swap_amount = int(balance * SWAP_PERCENTAGE)
                swap_result = self.swap_token(from_token, to_token, swap_amount)

                if swap_result:
                    results["swap"].append({
                        "from_token": from_token,
                        "to_token": to_token,
                        "amount": swap_amount,
                        "tx_hash": swap_result["transactionHash"].hex()
                    })

        # Update balances after swapping
        self.update_all_balances()

        # 3. Stake tokens
        for token_symbol in STAKING_ADDRESSES:
            balance = self.token_balances[token_symbol]["balance"]

            if balance > 0:
                stake_amount = int(balance * STAKE_PERCENTAGE)
                stake_result = self.stake_token(token_symbol, stake_amount)

                if stake_result:
                    results["stake"].append({
                        "token": token_symbol,
                        "amount": stake_amount,
                        "tx_hash": stake_result["transactionHash"].hex()
                    })

        # Final balance update
        self.update_all_balances()

        return results

    def run_single_operation(self, operation: str, token_symbol: str, amount: int = None) -> Dict[str, Any]:
        """Run a single operation (mint, swap, or stake)."""
        if operation not in ["mint", "swap", "stake"]:
            raise ValueError(f"Unknown operation: {operation}")

        if token_symbol not in TOKEN_ADDRESSES:
            raise ValueError(f"Unknown token symbol: {token_symbol}")

        # Update balance
        self.update_all_balances()

        # If amount is not specified, use a percentage of the balance
        if amount is None:
            if operation == "mint":
                amount = MIN_BALANCE.get(token_symbol, 0) * 2
            else:
                balance = self.token_balances[token_symbol]["balance"]
                percentage = SWAP_PERCENTAGE if operation == "swap" else STAKE_PERCENTAGE
                amount = int(balance * percentage)

        # Execute operation
        if operation == "mint":
            return self.mint_token(token_symbol, amount)
        elif operation == "swap":
            to_token = SWAP_PAIRS.get(token_symbol)
            if not to_token:
                raise ValueError(f"No swap pair found for {token_symbol}")
            return self.swap_token(token_symbol, to_token, amount)
        else:  # stake
            return self.stake_token(token_symbol, amount)

    def run_maitrix_sequence(self) -> Dict[str, List[Dict[str, Any]]]:
        """Run the specific sequence of operations based on transaction history."""
        results = {
            "approve": [],
            "swap": [],
            "stake": []
        }

        # Update balances
        self.update_all_balances()

        # 1. Approve VANA for swap
        vana_amount = int(float(self.token_balances["VANA"]["balance"]) * 0.4)
        if vana_amount > 0:
            vana_approve_result = self.approve_token("VANA", SWAP_ADDRESSES["VANA_TO_VANAUSD"], vana_amount)
            if vana_approve_result:
                results["approve"].append({
                    "token": "VANA",
                    "spender": SWAP_ADDRESSES["VANA_TO_VANAUSD"],
                    "amount": vana_amount,
                    "tx_hash": vana_approve_result["transactionHash"].hex()
                })

        # 2. Stake AUSD
        ausd_amount = int(float(self.token_balances["AUSD"]["balance"]) * 0.5)
        if ausd_amount > 0:
            ausd_stake_result = self.stake_token("AUSD", ausd_amount)
            if ausd_stake_result:
                results["stake"].append({
                    "token": "AUSD",
                    "pool": STAKING_ADDRESSES["AUSD"],
                    "amount": ausd_amount,
                    "tx_hash": ausd_stake_result["transactionHash"].hex()
                })

        # 3. Swap ATH to AUSD
        ath_amount = int(float(self.token_balances["ATH"]["balance"]) * 0.2)
        if ath_amount > 0:
            ath_swap_result = self.swap_token("ATH", "AUSD", ath_amount)
            if ath_swap_result:
                results["swap"].append({
                    "from_token": "ATH",
                    "to_token": "AUSD",
                    "amount": ath_amount,
                    "tx_hash": ath_swap_result["transactionHash"].hex()
                })

        # Update balances after swap
        self.update_all_balances()

        # 4. Swap VANA to VANAUSD
        vana_amount = int(float(self.token_balances["VANA"]["balance"]) * 0.2)
        if vana_amount > 0:
            vana_swap_result = self.swap_token("VANA", "VANAUSD", vana_amount)
            if vana_swap_result:
                results["swap"].append({
                    "from_token": "VANA",
                    "to_token": "VANAUSD",
                    "amount": vana_amount,
                    "tx_hash": vana_swap_result["transactionHash"].hex()
                })

        # Update balances after swap
        self.update_all_balances()

        # 5. Stake VUSD
        vusd_amount = int(float(self.token_balances["VUSD"]["balance"]) * 0.5)
        if vusd_amount > 0:
            vusd_stake_result = self.stake_token("VUSD", vusd_amount)
            if vusd_stake_result:
                results["stake"].append({
                    "token": "VUSD",
                    "pool": STAKING_ADDRESSES["VUSD"],
                    "amount": vusd_amount,
                    "tx_hash": vusd_stake_result["transactionHash"].hex()
                })

        # 6. Stake AUSD again
        ausd_amount = int(float(self.token_balances["AUSD"]["balance"]) * 0.5)
        if ausd_amount > 0:
            ausd_stake_result = self.stake_token("AUSD", ausd_amount)
            if ausd_stake_result:
                results["stake"].append({
                    "token": "AUSD",
                    "pool": STAKING_ADDRESSES["AUSD"],
                    "amount": ausd_amount,
                    "tx_hash": ausd_stake_result["transactionHash"].hex()
                })

        # 7. Stake in POOL1
        # For simplicity, we'll use ATH for this pool
        ath_amount = int(float(self.token_balances["ATH"]["balance"]) * 0.1)
        if ath_amount > 0:
            # Approve ATH for POOL1
            self.approve_token("ATH", STAKING_ADDRESSES["POOL1"], ath_amount)

            # Create a contract for POOL1
            pool1_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(STAKING_ADDRESSES["POOL1"]),
                abi=STAKE_TOKEN_ABI
            )

            # Stake ATH in POOL1
            tx_data = pool1_contract.functions.stake(ath_amount).build_transaction({
                "from": self.address,
                "nonce": self.web3.eth.get_transaction_count(self.address),
            })

            pool1_stake_result = send_transaction(self.web3, self.account, tx_data)
            if pool1_stake_result:
                results["stake"].append({
                    "token": "ATH",
                    "pool": STAKING_ADDRESSES["POOL1"],
                    "amount": ath_amount,
                    "tx_hash": pool1_stake_result["transactionHash"].hex()
                })

        # 8. Stake in POOL2
        # For simplicity, we'll use ATH for this pool too
        ath_amount = int(float(self.token_balances["ATH"]["balance"]) * 0.1)
        if ath_amount > 0:
            # Approve ATH for POOL2
            self.approve_token("ATH", STAKING_ADDRESSES["POOL2"], ath_amount)

            # Create a contract for POOL2
            pool2_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(STAKING_ADDRESSES["POOL2"]),
                abi=STAKE_TOKEN_ABI
            )

            # Stake ATH in POOL2
            tx_data = pool2_contract.functions.stake(ath_amount).build_transaction({
                "from": self.address,
                "nonce": self.web3.eth.get_transaction_count(self.address),
            })

            pool2_stake_result = send_transaction(self.web3, self.account, tx_data)
            if pool2_stake_result:
                results["stake"].append({
                    "token": "ATH",
                    "pool": STAKING_ADDRESSES["POOL2"],
                    "amount": ath_amount,
                    "tx_hash": pool2_stake_result["transactionHash"].hex()
                })

        # 9. Approve VANAUSD
        vanausd_amount = int(float(self.token_balances["VANAUSD"]["balance"]) * 0.5)
        if vanausd_amount > 0:
            vanausd_approve_result = self.approve_token("VANAUSD", TOKEN_ADDRESSES["VANAUSD"], vanausd_amount)
            if vanausd_approve_result:
                results["approve"].append({
                    "token": "VANAUSD",
                    "spender": TOKEN_ADDRESSES["VANAUSD"],
                    "amount": vanausd_amount,
                    "tx_hash": vanausd_approve_result["transactionHash"].hex()
                })

        # 10. Stake in POOL3
        # For simplicity, we'll use ATH for this pool too
        ath_amount = int(float(self.token_balances["ATH"]["balance"]) * 0.1)
        if ath_amount > 0:
            # Approve ATH for POOL3
            self.approve_token("ATH", STAKING_ADDRESSES["POOL3"], ath_amount)

            # Create a contract for POOL3
            pool3_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(STAKING_ADDRESSES["POOL3"]),
                abi=STAKE_TOKEN_ABI
            )

            # Stake ATH in POOL3
            tx_data = pool3_contract.functions.stake(ath_amount).build_transaction({
                "from": self.address,
                "nonce": self.web3.eth.get_transaction_count(self.address),
            })

            pool3_stake_result = send_transaction(self.web3, self.account, tx_data)
            if pool3_stake_result:
                results["stake"].append({
                    "token": "ATH",
                    "pool": STAKING_ADDRESSES["POOL3"],
                    "amount": ath_amount,
                    "tx_hash": pool3_stake_result["transactionHash"].hex()
                })

        # Final balance update
        self.update_all_balances()

        return results
