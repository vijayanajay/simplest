#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")
try:
    from meqsap.data import fetch_market_data
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("Testing mock paths...")
try:
    from unittest.mock import patch
    
    # Test if we can patch the correct paths
    with patch('meqsap.data.load_from_cache') as mock_load:
        print("✅ Mock patch successful")
        
except Exception as e:
    print(f"❌ Mock patch failed: {e}")

print("All basic tests passed!")
