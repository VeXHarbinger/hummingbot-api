"""
PancakeSwap V3 Direct Swap Service

This service provides direct interaction with PancakeSwap V3 contracts on BSC,
bypassing Gateway due to lack of router support.

Contracts:
- SwapRouter: 0x1b81D678ffb9C0263b24A97847620C99d213eB14
- Quoter: 0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997
"""
import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount

logger = logging.getLogger(__name__)

# BSC Mainnet RPC
BSC_RPC = "https://bsc-dataseed.binance.org/"

# PancakeSwap V3 Contract Addresses (BSC)
ROUTER_ADDRESS = "0x1b81D678ffb9C0263b24A97847620C99d213eB14"
QUOTER_ADDRESS = "0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997"

# Token Addresses (BSC)
# From pool 0xbc0E5A205D729299D93973d634E2507CD8b625A3
COAI_ADDRESS = "0x0A8D6C86e1bcE73fE4D0bD531e1a567306836EA5"  # Token0 in pool
USDT_ADDRESS = "0x55d398326f99059fF775485246999027B3197955"  # Token1 in pool
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

# Pool Fee (0.25% = 2500)
POOL_FEE = 2500

# ABIs (minimal required functions)
# PancakeSwap V3 QuoterV2 - uses quoteExactInputSingle with different signature
QUOTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IQuoterV2.QuoteExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
            {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
            {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "refundETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]


class PancakeSwapSwapService:
    """Direct PancakeSwap V3 swap service"""
    
    def __init__(self, private_key: str):
        """
        Initialize swap service with wallet private key.
        
        Args:
            private_key: Wallet private key (with or without 0x prefix)
        """
        self.w3 = Web3(Web3.HTTPProvider(BSC_RPC))
        
        # Setup account
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        self.account: LocalAccount = Account.from_key(private_key)
        
        # Initialize contracts
        self.quoter = self.w3.eth.contract(
            address=Web3.to_checksum_address(QUOTER_ADDRESS),
            abi=QUOTER_ABI
        )
        
        self.router = self.w3.eth.contract(
            address=Web3.to_checksum_address(ROUTER_ADDRESS),
            abi=ROUTER_ABI
        )
        
        logger.info(f"Initialized PancakeSwap swap service for wallet {self.account.address}")
    
    def _get_token_contract(self, token_address: str):
        """Get ERC20 token contract"""
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
    
    def get_token_decimals(self, token_address: str) -> int:
        """Get token decimals"""
        token = self._get_token_contract(token_address)
        return token.functions.decimals().call()
    
    def get_token_balance(self, token_address: str, wallet_address: Optional[str] = None) -> Decimal:
        """
        Get token balance.
        
        Args:
            token_address: Token contract address
            wallet_address: Wallet to check (defaults to service wallet)
        
        Returns:
            Balance in token units (human-readable)
        """
        if wallet_address is None:
            wallet_address = self.account.address
        
        token = self._get_token_contract(token_address)
        decimals = self.get_token_decimals(token_address)
        
        balance_wei = token.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        
        return Decimal(balance_wei) / Decimal(10 ** decimals)
    
    def quote_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_pct: Decimal = Decimal("1.0")
    ) -> Dict:
        """
        Get swap quote.
        
        Args:
            token_in: Input token address (e.g., COAI_ADDRESS)
            token_out: Output token address (e.g., USDT_ADDRESS)
            amount_in: Amount to swap (human-readable)
            slippage_pct: Slippage tolerance percentage
        
        Returns:
            {
                "amount_in": Decimal,
                "amount_out": Decimal,
                "amount_out_min": Decimal (with slippage),
                "price": Decimal,
                "gas_estimate": int
            }
        """
        try:
            # Get decimals
            decimals_in = self.get_token_decimals(token_in)
            decimals_out = self.get_token_decimals(token_out)
            
            # Convert to wei
            amount_in_wei = int(amount_in * Decimal(10 ** decimals_in))
            
            # Get quote from Quoter contract (PancakeSwap V3 uses QuoterV2 with struct params)
            params = {
                'tokenIn': Web3.to_checksum_address(token_in),
                'tokenOut': Web3.to_checksum_address(token_out),
                'amountIn': amount_in_wei,
                'fee': POOL_FEE,
                'sqrtPriceLimitX96': 0
            }
            
            result = self.quoter.functions.quoteExactInputSingle(params).call()
            
            amount_out_wei = result[0]
            gas_estimate = result[3] if len(result) > 3 else 300000
            
            # Convert to human-readable
            amount_out = Decimal(amount_out_wei) / Decimal(10 ** decimals_out)
            
            # Calculate minimum with slippage
            amount_out_min = amount_out * (Decimal("100") - slippage_pct) / Decimal("100")
            
            # Calculate price
            price = amount_out / amount_in if amount_in > 0 else Decimal("0")
            
            return {
                "amount_in": amount_in,
                "amount_out": amount_out,
                "amount_out_min": amount_out_min,
                "price": price,
                "gas_estimate": int(gas_estimate)
            }
            
        except Exception as e:
            logger.error(f"Error getting swap quote: {e}")
            raise
    
    def approve_token(
        self,
        token_address: str,
        spender_address: str,
        amount: Optional[Decimal] = None
    ) -> str:
        """
        Approve token spending.
        
        Args:
            token_address: Token to approve
            spender_address: Spender (usually router)
            amount: Amount to approve (None = unlimited)
        
        Returns:
            Transaction hash
        """
        token = self._get_token_contract(token_address)
        decimals = self.get_token_decimals(token_address)
        
        # Check current allowance
        current_allowance = token.functions.allowance(
            self.account.address,
            Web3.to_checksum_address(spender_address)
        ).call()
        
        # Determine approval amount
        if amount is None:
            # Unlimited approval
            approve_amount = 2**256 - 1
        else:
            approve_amount = int(amount * Decimal(10 ** decimals))
        
        # Only approve if needed
        if current_allowance >= approve_amount:
            logger.info(f"Token already approved (allowance: {current_allowance})")
            return None
        
        logger.info(f"Approving {approve_amount} tokens...")
        
        # Build transaction
        tx = token.functions.approve(
            Web3.to_checksum_address(spender_address),
            approve_amount
        ).build_transaction({
            'from': self.account.address,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            logger.info(f"Approval successful: {tx_hash.hex()}")
            return tx_hash.hex()
        else:
            raise Exception(f"Approval failed: {tx_hash.hex()}")
    
    def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        slippage_pct: Decimal = Decimal("1.0")
    ) -> Dict:
        """
        Execute swap.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount to swap (human-readable)
            slippage_pct: Slippage tolerance percentage
        
        Returns:
            {
                "transaction_hash": str,
                "amount_in": Decimal,
                "amount_out": Decimal,
                "price": Decimal
            }
        """
        try:
            # Get quote first
            quote = self.quote_swap(token_in, token_out, amount_in, slippage_pct)
            
            logger.info(f"Executing swap: {amount_in} → {quote['amount_out']} (min: {quote['amount_out_min']})")
            
            # Get decimals
            decimals_in = self.get_token_decimals(token_in)
            decimals_out = self.get_token_decimals(token_out)
            
            # Approve token if needed
            approve_tx = self.approve_token(token_in, ROUTER_ADDRESS, amount_in)
            if approve_tx:
                logger.info(f"Token approved: {approve_tx}")
            
            # Convert to wei
            amount_in_wei = int(amount_in * Decimal(10 ** decimals_in))
            amount_out_min_wei = int(quote['amount_out_min'] * Decimal(10 ** decimals_out))
            
            # Build swap transaction
            swap_params = {
                'tokenIn': Web3.to_checksum_address(token_in),
                'tokenOut': Web3.to_checksum_address(token_out),
                'fee': POOL_FEE,
                'recipient': self.account.address,
                'amountIn': amount_in_wei,
                'amountOutMinimum': amount_out_min_wei,
                'sqrtPriceLimitX96': 0
            }
            
            tx = self.router.functions.exactInputSingle(
                swap_params
            ).build_transaction({
                'from': self.account.address,
                'gas': quote['gas_estimate'] + 50000,  # Add buffer
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'value': 0
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"Swap transaction sent: {tx_hash.hex()}")
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 1:
                logger.info(f"Swap successful: {tx_hash.hex()}")
                
                return {
                    "transaction_hash": tx_hash.hex(),
                    "amount_in": amount_in,
                    "amount_out": quote['amount_out'],
                    "price": quote['price'],
                    "gas_used": receipt['gasUsed']
                }
            else:
                raise Exception(f"Swap transaction failed: {tx_hash.hex()}")
                
        except Exception as e:
            logger.error(f"Error executing swap: {e}")
            raise


# Helper function for easy COAI-USDT swaps
def swap_coai_to_usdt(private_key: str, coai_amount: Decimal, slippage_pct: Decimal = Decimal("1.0")) -> Dict:
    """
    Convenience function to swap COAI → USDT.
    
    Args:
        private_key: Wallet private key
        coai_amount: Amount of COAI to swap
        slippage_pct: Slippage tolerance
    
    Returns:
        Swap result with transaction hash
    """
    service = PancakeSwapSwapService(private_key)
    return service.execute_swap(COAI_ADDRESS, USDT_ADDRESS, coai_amount, slippage_pct)


def swap_usdt_to_coai(private_key: str, usdt_amount: Decimal, slippage_pct: Decimal = Decimal("1.0")) -> Dict:
    """
    Convenience function to swap USDT → COAI.
    
    Args:
        private_key: Wallet private key
        usdt_amount: Amount of USDT to swap
        slippage_pct: Slippage tolerance
    
    Returns:
        Swap result with transaction hash
    """
    service = PancakeSwapSwapService(private_key)
    return service.execute_swap(USDT_ADDRESS, COAI_ADDRESS, usdt_amount, slippage_pct)
