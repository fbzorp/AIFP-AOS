#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for development using Python cryptography library.
This avoids requiring OpenSSL to be installed on the host system.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: cryptography library not installed")
    print("Install with: pip install cryptography")
    sys.exit(1)

def generate_ssl_cert(domain, cert_dir="nginx/ssl", days_valid=365):
    """Generate self-signed SSL certificate using Python cryptography."""
    
    # Get domain from environment variable if not provided
    if domain is None or domain == "None":
        domain = os.environ.get("DOMAIN", "staging.aifp-aos.local")
    
    # Create directory if it doesn't exist
    cert_path = Path(cert_dir)
    cert_path.mkdir(parents=True, exist_ok=True)
    
    # Define certificate paths
    private_key_path = cert_path / "privkey.pem"
    cert_path_obj = cert_path / "fullchain.pem"
    
    # Check if certificates already exist (idempotency)
    if private_key_path.exists() and cert_path_obj.exists():
        print("SSL certificates already exist, skipping generation")
        print(f"Private key: {private_key_path}")
        print(f"Certificate: {cert_path_obj}")
        return
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "DevCity"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "AiFinPay"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Development"),
        x509.NameAttribute(NameOID.COMMON_NAME, domain),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.now(timezone.utc)
    ).not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=days_valid)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(domain),
            x509.DNSName(f"www.{domain}"),
            x509.DNSName("localhost"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write private key
    with open(private_key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    
    # Write certificate
    with open(cert_path_obj, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    print(f"SSL certificates generated successfully!")
    print(f"Private key: {private_key_path}")
    print(f"Certificate: {cert_path_obj}")
    print(f"Domain: {domain}")
    print(f"Valid for: {days_valid} days")
    print()
    print("WARNING: These are self-signed certificates for development only!")
    print("Do NOT use them in production.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate self-signed SSL certificates")
    parser.add_argument("domain", nargs="?", default=None, help="Domain name for the certificate")
    parser.add_argument("--cert-dir", default="nginx/ssl", help="Directory to save certificates")
    parser.add_argument("--days", type=int, default=365, help="Number of days the certificate is valid")
    
    args = parser.parse_args()
    
    generate_ssl_cert(args.domain, args.cert_dir, args.days)
