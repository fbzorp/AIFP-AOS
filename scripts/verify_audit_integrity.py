#!/usr/bin/env python3
"""
Audit Integrity Verification Script

Verifies the tamper-resistant audit event chain by recomputing hashes
and checking for any breaks in the chain.

Usage:
    python scripts/verify_audit_integrity.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.core.audit.service import verify_audit_chain
from apps.models.base import get_sync_session


def main():
    """Main verification function."""
    print("=" * 60)
    print("AUDIT INTEGRITY VERIFICATION")
    print("=" * 60)
    
    try:
        with get_sync_session() as session:
            result = verify_audit_chain(session)
            
            print(f"\nTotal records checked: {result['total_records']}")
            print(f"Broken records found: {result['broken_records']}")
            
            if result['valid']:
                print("\n✅ AUDIT CHAIN IS VALID")
                print("   All hashes match and chain is intact.")
                return 0
            else:
                print(f"\n❌ AUDIT CHAIN IS BROKEN")
                if result.get('first_broken_id'):
                    print(f"   First broken record ID: {result['first_broken_id']}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
                return 1
                
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED")
        print(f"   Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
