#!/usr/bin/env python3
"""Offline demonstration: JSON reserialization changes signed webhook bytes.

Synthetic data and fictional key only. Not a provider-specific verifier.
"""
import hashlib
import hmac
import json


def verify(raw_body, signature, key):
    expected = hmac.new(key, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def main():
    key = b'fictional-fixture-key-not-a-production-secret'
    raw = b'{"event_id":"fixture_001", "type":"example.updated", "data":{"value":1}}'
    signature = hmac.new(key, raw, hashlib.sha256).hexdigest()
    reconstructed = json.dumps(json.loads(raw), sort_keys=True).encode()
    assert verify(raw, signature, key)
    assert not verify(reconstructed, signature, key)
    print('Original raw body: signature valid')
    print('Parsed and reserialized JSON: signature invalid')
    print('Fix: verify original raw bytes before parsing; use provider-specific verification rules.')
    print('Synthetic fixture only. No network requests were made.')


if __name__ == '__main__':
    main()
