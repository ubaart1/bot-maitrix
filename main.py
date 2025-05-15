#!/usr/bin/env python3
"""
MAITRIX Bot - Automate mint → swap → stake operations on MAITRIX testnet.

Usage:
    python main.py auto                  # Run the full automation cycle
    python main.py balance               # Check token balances
    python main.py mint <token> <amount> # Mint a specific token
    python main.py swap <token> <amount> # Swap a specific token
    python main.py stake <token> <amount> # Stake a specific token
"""

import sys
import logging
import argparse
from decimal import Decimal

from utils import load_env, setup_web3
from bot import MaitrixBot
from config import TOKEN_ADDRESSES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def parse_amount(amount_str: str, decimals: int) -> int:
    """Parse amount string to integer with proper decimals."""
    try:
        # Handle scientific notation and decimal points
        amount_decimal = Decimal(amount_str)
        return int(amount_decimal * (10 ** decimals))
    except Exception as e:
        logger.error(f"Failed to parse amount: {amount_str}")
        raise ValueError(f"Invalid amount format: {amount_str}") from e

def main():
    """Main entry point."""
    # Print banner
    print("=" * 80)
    print("MAITRIX Bot - Automate mint → swap → stake operations on MAITRIX testnet")
    print("=" * 80)

    parser = argparse.ArgumentParser(description="MAITRIX Bot - Automate mint → swap → stake operations")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Auto command
    auto_parser = subparsers.add_parser("auto", help="Run the full automation cycle")

    # Maitrix sequence command
    maitrix_parser = subparsers.add_parser("maitrix", help="Run the specific sequence of operations based on transaction history")

    # Balance command
    balance_parser = subparsers.add_parser("balance", help="Check token balances")

    # Mint command
    mint_parser = subparsers.add_parser("mint", help="Mint a specific token")
    mint_parser.add_argument("token", choices=TOKEN_ADDRESSES.keys(), help="Token symbol")
    mint_parser.add_argument("amount", nargs="?", help="Amount to mint (default: 2x minimum balance)")

    # Swap command
    swap_parser = subparsers.add_parser("swap", help="Swap a specific token")
    swap_parser.add_argument("token", choices=TOKEN_ADDRESSES.keys(), help="Token symbol to swap from")
    swap_parser.add_argument("amount", nargs="?", help="Amount to swap (default: 30% of balance)")

    # Stake command
    stake_parser = subparsers.add_parser("stake", help="Stake a specific token")
    stake_parser.add_argument("token", choices=TOKEN_ADDRESSES.keys(), help="Token symbol to stake")
    stake_parser.add_argument("amount", nargs="?", help="Amount to stake (default: 50% of balance)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        # Load environment variables
        load_env()

        # Set up Web3 connection and account
        web3, account = setup_web3()

        # Display wallet address
        print(f"\nUsing wallet address: {account.address}")
        print(f"Network: Arbitrum Sepolia (Chain ID: 421614)")
        print("-" * 80)

        # Initialize bot
        bot = MaitrixBot(web3, account)

        # Execute command
        if args.command == "auto":
            logger.info("Running full automation cycle...")
            results = bot.run_auto_cycle()

            # Print results
            for operation, txs in results.items():
                if txs:
                    logger.info(f"{operation.capitalize()} operations:")
                    for tx in txs:
                        if operation == "swap":
                            logger.info(f"  Swapped {tx['from_token']} to {tx['to_token']}: "
                                       f"Amount: {tx['amount']}, TX: {tx['tx_hash']}")
                        else:
                            logger.info(f"  {tx['token']}: Amount: {tx['amount']}, TX: {tx['tx_hash']}")

            logger.info("Automation cycle completed.")

        elif args.command == "maitrix":
            logger.info("Running MAITRIX sequence based on transaction history...")
            results = bot.run_maitrix_sequence()

            # Print results
            for operation, txs in results.items():
                if txs:
                    logger.info(f"{operation.capitalize()} operations:")
                    for tx in txs:
                        if operation == "swap":
                            logger.info(f"  Swapped {tx['from_token']} to {tx['to_token']}: "
                                       f"Amount: {tx['amount']}, TX: {tx['tx_hash']}")
                        elif operation == "approve":
                            logger.info(f"  Approved {tx['token']} for {tx['spender']}: "
                                       f"Amount: {tx['amount']}, TX: {tx['tx_hash']}")
                        else:  # stake
                            logger.info(f"  Staked {tx['token']} in {tx['pool']}: "
                                       f"Amount: {tx['amount']}, TX: {tx['tx_hash']}")

            logger.info("MAITRIX sequence completed.")

        elif args.command == "balance":
            logger.info("Checking token balances...")
            bot.update_all_balances()

            for symbol, data in bot.token_balances.items():
                logger.info(f"{symbol}: {data['formatted']}")

        else:  # mint, swap, or stake
            token = args.token
            amount = None

            if args.amount:
                # Get token decimals
                decimals = bot.token_balances[token]["decimals"]
                amount = parse_amount(args.amount, decimals)

            logger.info(f"Running {args.command} operation for {token}...")
            result = bot.run_single_operation(args.command, token, amount)

            if result:
                logger.info(f"{args.command.capitalize()} operation successful.")
                logger.info(f"Transaction hash: {result['transactionHash'].hex()}")
            else:
                logger.warning(f"{args.command.capitalize()} operation failed or not needed.")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
