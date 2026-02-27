# Changelog

All notable changes to langchain-onely will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-02-27

### Changed
- Improved HTTP response handling for non-JSON and empty responses
- Standardized timeouts and User-Agent versioning
- Removed internal-only artifacts from the public package
- Documentation refreshed for production release
- Fixed EVM (Base) x402 signing to use official exact scheme (EIP-3009)
- Added payment selection inputs (`preferredNetwork`, `preferredAsset`, `allowFallback`)

## [0.1.0] - 2026-02-27

### Added
- Initial release of langchain-onely
- 9 LangChain tools for buying and selling APIs
- Support for x402 micropayment protocol
- Multi-chain support (Solana and Base networks)
- Automatic payment signing with eth-account and solders
- Custom RPC URL support for both Base and Solana
- Comprehensive error handling with structured responses
- Full documentation

### Buyer Tools
- `onely_search` - Search for APIs on 1ly marketplace
- `onely_get_details` - Get API listing details
- `onely_call` - Automatically pay for and call APIs
- `onely_review` - Leave reviews for purchased APIs

### Seller Tools
- `onely_create_store` - Create your API store
- `onely_create_link` - List APIs for sale
- `onely_list_links` - View your API listings
- `onely_get_stats` - Check earnings and statistics
- `onely_withdraw` - Withdraw earnings to Solana wallet

### Features
- x402 payment protocol integration
- EIP-712 signing for Base/EVM payments
- SPL token transfers for Solana payments
- Dynamic token decimals fetching
- Partial transaction signing with NullSigner
- Multi-network payment selector
- Retry logic with exponential backoff
- Rate limit handling

### Security
- Non-custodial wallet management
- No hardcoded secrets or API keys
- Input validation on all tools
- Secure transaction signing

[0.1.1]: https://github.com/1lystore/langchain-onely/releases/tag/v0.1.1
[0.1.0]: https://github.com/1lystore/langchain-onely/releases/tag/v0.1.0
