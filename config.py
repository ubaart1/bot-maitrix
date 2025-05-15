"""
Configuration file for the MAITRIX bot.
Contains contract addresses, ABIs, and other settings.
"""

# Network configuration
CHAIN_ID = 421614  # Arbitrum Sepolia
RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"

# Gas settings
GAS_PRICE_GWEI = 1.5
GAS_LIMIT = 3000000

# Transaction settings
TX_CONFIRMATIONS = 2
TX_TIMEOUT = 300  # seconds

# Token contract addresses
TOKEN_ADDRESSES = {
    "ATH": "0x1428444eacdc0fd115dd4318fce65b61cd1ef399",
    "USDe": "0xf4be938070f59764c85face374f92a4670ff3877",
    "LVLUSD": "0x8802b7bcf8eedcc9e1ba6c20e139bee89dd98e83",
    "VANA": "0xbebf4e25652e7f23ccdcccaacb32004501c4bff8",
    "AUSD": "0x78de28aabbd5198657b26a8dc9777f441551b477",
    "VUSD": "0xc14a8e2fc341a97a57524000bf0f7f1ba4de4802",
    "VANAUSD": "0x46a6585a0ad1750d37b4e6810eb59cbdf591dc30",
}

# Faucet contract addresses
FAUCET_ADDRESSES = {
    "LVLUSD": "0x8c65a8736bdE6A2D3b7068316d027cE17f6b587C",
}

# Staking pool contract addresses
STAKING_ADDRESSES = {
    "AUSD": "0x054de909723ECda2d119E31583D40a52a332f85c",
    "VUSD": "0x5bb9Fa02a3DCCDB4E9099b48e8Ba5841D2e59d51",
    "POOL1": "0x3988053b7c748023a1ae19a8ed4c1bf217932bdb",
    "POOL2": "0x5de3fbd40d4c3892914c3b67b5b529d776a1483a",
    "POOL3": "0x2608a88219bfb34519f635dd9ca2ae971539ca60",
}

# Swap/Router contract addresses
SWAP_ADDRESSES = {
    "ATH_TO_AUSD": "0x2cFDeE1d5f04dD235AEA47E1aD2fB66e3A61C13e",
    "VANA_TO_VANAUSD": "0xEfbAE3A68b17a61f21C7809Edfa8Aa3CA7B2546f",
    "MINT_SPECIAL": "0x3dcaca90a714498624067948c092dd0373f08265",
}

# Token pairs for swapping
SWAP_PAIRS = {
    "ATH": "AUSD",
    "VANA": "VANAUSD",
}

# Minimum token balances to trigger actions
MIN_BALANCE = {
    "ATH": 1 * 10**18,  # 1 ATH
    "USDe": 1 * 10**18,  # 1 USDe
    "LVLUSD": 1 * 10**18,  # 1 LVLUSD
    "VANA": 1 * 10**18,  # 1 VANA
    "AUSD": 1 * 10**18,  # 1 AUSD
    "VUSD": 1 * 10**18,  # 1 VUSD
    "VANAUSD": 1 * 10**18,  # 1 VANAUSD
}

# Percentage of token balance to swap/stake (0.1 = 10%)
SWAP_PERCENTAGE = 0.3
STAKE_PERCENTAGE = 0.5

# ABIs
# Common ERC20 ABI with approve function
ERC20_ABI = [
    {
        "name": "approve",
        "type": "function",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "outputs": [{"type": "bool"}]
    },
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}]
    },
    {
        "name": "decimals",
        "type": "function",
        "inputs": [],
        "outputs": [{"type": "uint8"}]
    },
    {
        "name": "symbol",
        "type": "function",
        "inputs": [],
        "outputs": [{"type": "string"}]
    },
    {
        "name": "allowance",
        "type": "function",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "outputs": [{"type": "uint256"}]
    }
]

# Mint function ABI
MINT_ABI = [
    {
        "name": "mint",
        "type": "function",
        "inputs": [{"name": "amount", "type": "uint256"}],
        "outputs": []
    }
]

# Stake function ABI
STAKE_ABI = [
    {
        "name": "stake",
        "type": "function",
        "inputs": [{"name": "_tokens", "type": "uint256"}],
        "outputs": []
    }
]

# Special function ABIs based on transaction history
SPECIAL_FUNCTION_ABI = [
    {
        "name": "swapATHtoAUSD",
        "type": "function",
        "inputs": [{"name": "amount", "type": "uint256"}],
        "outputs": [],
        "signature": "0x1bf6318b"
    },
    {
        "name": "swapVANAtoVANAUSD",
        "type": "function",
        "inputs": [{"name": "amount", "type": "uint256"}],
        "outputs": [],
        "signature": "0xa6d67510"
    }
]

# Combined ABIs for different contract types
TOKEN_ABI = ERC20_ABI
MINT_TOKEN_ABI = ERC20_ABI + MINT_ABI
STAKE_TOKEN_ABI = ERC20_ABI + STAKE_ABI
SWAP_ATH_ABI = SPECIAL_FUNCTION_ABI[:1]  # swapATHtoAUSD
SWAP_VANA_ABI = SPECIAL_FUNCTION_ABI[1:]  # swapVANAtoVANAUSD

# Explorer URL for transaction links
EXPLORER_URL = "https://sepolia.arbiscan.io/tx/"
