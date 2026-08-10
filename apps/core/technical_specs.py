"""
AiFinPay technical specifications for content verification.
Contains known-good reference data for verifying technical claims.
"""

# Known-good API endpoints
VALID_ENDPOINTS = {
    "agent_address",
    "agent_quote", 
    "quote_split",
    "payable_fetch",
    "agent_call",
    "agent_claim_self",
    "get_balance",
    "get_status"
}

# Supported networks
SUPPORTED_NETWORKS = {
    "devnet",
    "mainnet", 
    "testnet",
    "base-sepolia",
    "solana-devnet"
}

# Supported transaction types
SUPPORTED_TRANSACTION_TYPES = {
    "payment",
    "quote",
    "split",
    "claim",
    "fetch"
}

# Known integrations
KNOWN_INTEGRATIONS = {
    "mcp",
    "x402",
    "sdk",
    "rest_api",
    "websocket"
}

# Configuration fields
VALID_CONFIG_FIELDS = {
    "network",
    "rpc_url", 
    "private_key",
    "agent_secret",
    "max_usd",
    "timeout"
}

def verify_endpoint_claim(endpoint: str) -> bool:
    """Verify if an endpoint name is valid."""
    return endpoint in VALID_ENDPOINTS

def verify_network_claim(network: str) -> bool:
    """Verify if a network is supported."""
    return network.lower() in SUPPORTED_NETWORKS

def verify_integration_claim(integration: str) -> bool:
    """Verify if an integration is known."""
    return integration.lower() in KNOWN_INTEGRATIONS

def verify_transaction_type(transaction_type: str) -> bool:
    """Verify if a transaction type is supported."""
    return transaction_type.lower() in SUPPORTED_TRANSACTION_TYPES

def verify_config_field(field: str) -> bool:
    """Verify if a configuration field is valid."""
    return field in VALID_CONFIG_FIELDS

def extract_technical_claims(content: str) -> dict:
    """
    Extract potential technical claims from content for verification.
    Returns a dict with claim types and their values.
    """
    import re
    
    claims = {
        "endpoints": set(),
        "networks": set(),
        "integrations": set(),
        "transaction_types": set(),
        "config_fields": set()
    }
    
    # Simple pattern matching for common technical terms
    # This is a basic implementation - could be enhanced with NLP
    
    # Look for endpoint patterns
    endpoint_patterns = re.findall(r'\b(agent_address|agent_quote|quote_split|payable_fetch|agent_call|agent_claim_self|get_balance|get_status)\b', content, re.IGNORECASE)
    claims["endpoints"].update(endpoint_patterns)
    
    # Look for network patterns
    network_patterns = re.findall(r'\b(devnet|mainnet|testnet|base-sepolia|solana-devnet)\b', content, re.IGNORECASE)
    claims["networks"].update(network_patterns)
    
    # Look for integration patterns
    integration_patterns = re.findall(r'\b(mcp|x402|sdk|rest_api|websocket)\b', content, re.IGNORECASE)
    claims["integrations"].update(integration_patterns)
    
    # Look for transaction type patterns
    tx_patterns = re.findall(r'\b(payment|quote|split|claim|fetch)\b', content, re.IGNORECASE)
    claims["transaction_types"].update(tx_patterns)
    
    return claims

def verify_technical_content(content: str) -> dict:
    """
    Verify technical content against known-good specifications.
    Returns verification results with status and details.
    """
    claims = extract_technical_claims(content)
    
    verification_results = {
        "status": "verified",
        "failed_claims": [],
        "verified_claims": [],
        "details": []
    }
    
    # Verify each claim type
    for endpoint in claims["endpoints"]:
        if verify_endpoint_claim(endpoint):
            verification_results["verified_claims"].append(f"endpoint: {endpoint}")
        else:
            verification_results["failed_claims"].append(f"endpoint: {endpoint}")
    
    for network in claims["networks"]:
        if verify_network_claim(network):
            verification_results["verified_claims"].append(f"network: {network}")
        else:
            verification_results["failed_claims"].append(f"network: {network}")
    
    for integration in claims["integrations"]:
        if verify_integration_claim(integration):
            verification_results["verified_claims"].append(f"integration: {integration}")
        else:
            verification_results["failed_claims"].append(f"integration: {integration}")
    
    for tx_type in claims["transaction_types"]:
        if verify_transaction_type(tx_type):
            verification_results["verified_claims"].append(f"transaction_type: {tx_type}")
        else:
            verification_results["failed_claims"].append(f"transaction_type: {tx_type}")
    
    # Determine overall status
    if verification_results["failed_claims"]:
        verification_results["status"] = "failed"
        verification_results["details"] = f"Found {len(verification_results['failed_claims'])} unverifiable technical claims"
    elif not verification_results["verified_claims"]:
        verification_results["status"] = "pending"  # No technical claims to verify
        verification_results["details"] = "No technical claims found for verification"
    else:
        verification_results["details"] = f"All {len(verification_results['verified_claims'])} technical claims verified"
    
    return verification_results
