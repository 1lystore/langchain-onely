"""x402 payment protocol implementation using x402 SDK."""

import base64
from typing import Any, Dict, Optional

import x402
from eth_account import Account
from solders.keypair import Keypair
from x402 import PaymentRequirements
from x402.http import x402HTTPClientSync
from x402.mechanisms.evm.exact.client import ExactEvmScheme as X402ExactEvmScheme
from x402.mechanisms.evm.signers import EthAccountSigner


class ExactSvmScheme:
    """Solana (SVM) payment scheme client for x402.

    Implements the "exact" scheme for Solana token payments.
    Creates a signed SPL token transfer transaction.
    This matches the @x402/svm/exact implementation from TypeScript.
    """

    scheme = "exact"

    def __init__(self, signer: Keypair, rpc_url: Optional[str] = None):
        """Initialize with a Solana keypair.

        Args:
            signer: Solders Keypair for signing payments
            rpc_url: Optional custom RPC URL (defaults to mainnet-beta)
        """
        self._signer = signer
        self._rpc_url = rpc_url or "https://api.mainnet-beta.solana.com"

    def create_payment_payload(self, requirements: PaymentRequirements) -> Dict[str, Any]:
        """Create payment payload for Solana payment.

        Creates a signed SPL token transfer transaction.

        Args:
            requirements: Payment requirements from 402 response

        Returns:
            Payment payload dict with base64-encoded transaction
        """
        import struct

        from solana.rpc.api import Client as SolanaClient
        from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
        from solders.instruction import AccountMeta, Instruction
        from solders.message import MessageV0
        from solders.null_signer import NullSigner
        from solders.pubkey import Pubkey
        from solders.transaction import VersionedTransaction

        # Get fee payer from extra
        fee_payer_str = requirements.extra.get("feePayer") if requirements.extra else None
        if not fee_payer_str:
            raise ValueError("feePayer required in payment requirements extra")

        fee_payer_pubkey = Pubkey.from_string(fee_payer_str)
        fee_payer_null_signer = NullSigner(fee_payer_pubkey)  # Placeholder for fee payer signature
        mint = Pubkey.from_string(requirements.asset)
        recipient = Pubkey.from_string(requirements.pay_to)
        sender = self._signer.pubkey()

        # Connect to Solana RPC
        client = SolanaClient(self._rpc_url)

        # Get mint info to determine token program and decimals
        mint_info = client.get_account_info(mint)
        if not mint_info.value:
            raise ValueError(f"Mint account not found: {mint}")

        # Parse mint data to get decimals
        # Mint account layout: decimals is at offset 44 (u8)
        mint_data = mint_info.value.data
        if len(mint_data) <= 44:
            raise ValueError(f"Invalid mint data length: {len(mint_data)}")

        decimals = mint_data[44]  # Get actual decimals from mint

        # Use standard Token program (SPL)
        TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        token_program = TOKEN_PROGRAM_ID

        # Derive Associated Token Accounts
        # ATA derivation: [b"associated-token-account", wallet, token_program, mint]
        ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string(
            "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
        )

        def find_ata(owner: Pubkey, mint_addr: Pubkey) -> Pubkey:
            """Find Associated Token Account address."""
            seeds = [bytes(owner), bytes(token_program), bytes(mint_addr)]
            pda, _ = Pubkey.find_program_address(seeds, ASSOCIATED_TOKEN_PROGRAM_ID)
            return pda

        source_ata = find_ata(sender, mint)
        destination_ata = find_ata(recipient, mint)

        # Build SPL Token TransferChecked instruction
        # Instruction discriminator for TransferChecked: 12
        amount = int(requirements.amount)

        # SPL Token TransferChecked instruction layout
        transfer_data = struct.pack("<BQB", 12, amount, decimals)

        transfer_ix = Instruction(
            program_id=token_program,
            accounts=[
                AccountMeta(source_ata, is_signer=False, is_writable=True),
                AccountMeta(mint, is_signer=False, is_writable=False),
                AccountMeta(destination_ata, is_signer=False, is_writable=True),
                AccountMeta(sender, is_signer=True, is_writable=False),
            ],
            data=transfer_data,
        )

        # Get latest blockhash
        blockhash_resp = client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        # Build compute budget instructions
        compute_unit_limit_ix = set_compute_unit_limit(8000)
        compute_unit_price_ix = set_compute_unit_price(1)

        # Build message
        instructions = [
            compute_unit_limit_ix,
            compute_unit_price_ix,
            transfer_ix,
        ]

        message = MessageV0.try_compile(
            payer=fee_payer_pubkey,
            instructions=instructions,
            address_lookup_table_accounts=[],
            recent_blockhash=blockhash,
        )

        # Create partially signed transaction
        # Fee payer uses NullSigner (placeholder), our keypair actually signs
        tx = VersionedTransaction(message, [fee_payer_null_signer, self._signer])

        # Serialize to wire format and encode as base64
        tx_bytes = bytes(tx)
        tx_base64 = base64.b64encode(tx_bytes).decode("utf-8")

        # Return payload with transaction
        return {"transaction": tx_base64}


class ExactEvmScheme:
    """EVM payment scheme client for x402 (Exact).

    Wraps the official x402 EVM exact client to ensure EIP-3009 compliance.
    """

    scheme = "exact"

    def __init__(self, signer: Account, rpc_url: Optional[str] = None):
        self._signer = signer
        self._rpc_url = rpc_url
        self._inner = X402ExactEvmScheme(EthAccountSigner(self._signer))

    def create_payment_payload(self, requirements: PaymentRequirements) -> Dict[str, Any]:
        return self._inner.create_payment_payload(requirements)


def create_payment_signature(
    payment_data: Dict[str, Any],
    base_wallet: Optional[Account] = None,
    solana_wallet: Optional[Keypair] = None,
    resource_url: str = "https://1ly.store/api",
    base_rpc_url: Optional[str] = None,
    solana_rpc_url: Optional[str] = None,
) -> str:
    """Create x402 payment signature using proper x402 SDK.

    This matches the MCP server implementation pattern:
    1. Parse 402 response to PaymentRequired
    2. Create x402Client with payment selector
    3. Register appropriate scheme (EVM or Solana)
    4. Use x402HTTPClient to create and encode payment payload

    Args:
        payment_data: Parsed 402 response body
        base_wallet: Base wallet for EVM payments
        solana_wallet: Solana wallet for Solana payments
        resource_url: URL being accessed
        base_rpc_url: Custom Base RPC URL (optional)
        solana_rpc_url: Custom Solana RPC URL (optional)

    Returns:
        Payment signature header value

    Raises:
        ValueError: If no wallet available or invalid payment data
    """
    if not base_wallet and not solana_wallet:
        raise ValueError("Either base_wallet or solana_wallet must be provided")

    # Parse accepts list
    accepts = payment_data.get("accepts", [])
    if not accepts:
        raise ValueError("No payment methods in 402 response")

    # Determine which wallet/network to use
    # Prefer Solana if we have solana_wallet and any accept supports Solana
    use_solana = False
    if solana_wallet:
        for accept in accepts:
            network = str(accept.get("network", ""))
            if network.startswith("solana:"):
                use_solana = True
                break

    # If not using Solana, check if we can use EVM
    if not use_solana:
        if not base_wallet:
            raise ValueError("Base wallet required for EVM payment")
        # Check if any accept supports EVM
        has_evm = any(str(accept.get("network", "")).startswith("eip155:") for accept in accepts)
        if not has_evm:
            raise ValueError("No compatible payment method found")

    # Create x402Client with payment selector
    # Simple selector: pick first matching network for the wallet type
    def payment_selector(resource, requirements_list):
        """Select payment requirement based on available wallet."""
        if use_solana:
            # Find any Solana network option
            for req in requirements_list:
                if req.network.startswith("solana:"):
                    return req
        else:
            # Find any EVM network option (prefer Base if available)
            for req in requirements_list:
                if req.network == "eip155:8453":  # Base mainnet
                    return req
            for req in requirements_list:
                if req.network.startswith("eip155:"):
                    return req
        # Fallback to first available
        return requirements_list[0] if requirements_list else None

    # Create x402ClientSync (synchronous version)
    client = x402.x402ClientSync(payment_requirements_selector=payment_selector)

    # Register appropriate scheme for all networks in accepts list
    if use_solana:
        # Register Solana scheme for all Solana networks in accepts
        scheme_client = ExactSvmScheme(solana_wallet, rpc_url=solana_rpc_url)
        for accept in accepts:
            network = accept.get("network", "")
            if network.startswith("solana:"):
                client.register(network, scheme_client)
        # Also register common Solana networks as fallback
        client.register("solana:mainnet", scheme_client)
        client.register("solana:devnet", scheme_client)
        client.register("solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp", scheme_client)  # mainnet-beta
    else:
        # Register EVM scheme for all EVM networks in accepts
        scheme_client = ExactEvmScheme(base_wallet, rpc_url=base_rpc_url)
        for accept in accepts:
            network = accept.get("network", "")
            if network.startswith("eip155:"):
                client.register(network, scheme_client)
        # Also register common EVM networks as fallback
        client.register("eip155:8453", scheme_client)  # Base
        client.register("eip155:1", scheme_client)  # Ethereum mainnet
        client.register("eip155:84532", scheme_client)  # Base Sepolia

    # Create HTTP client wrapper (synchronous version)
    http_client = x402HTTPClientSync(client)

    # Parse the 402 response into PaymentRequired object
    payment_required = x402.parse_payment_required(payment_data)

    # Create payment payload using the x402 SDK
    payment_payload = http_client.create_payment_payload(payment_required)

    # Encode to payment signature header
    headers = http_client.encode_payment_signature_header(payment_payload)

    # Return the payment signature header value
    # Try different header name variations
    return (
        headers.get("payment-signature")
        or headers.get("Payment-Signature")
        or headers.get("PAYMENT-SIGNATURE")
        or headers.get("x-payment")
        or headers.get("X-PAYMENT")
        or ""
    )


def parse_402_response(response_data: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Parse 402 Payment Required response.

    Args:
        response_data: JSON response body from 402
        headers: Response headers

    Returns:
        Parsed payment requirements
    """
    if not response_data:
        raise ValueError("402 response missing payment requirements")

    return response_data
