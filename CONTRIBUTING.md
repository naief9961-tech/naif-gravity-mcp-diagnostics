# Contributing

Useful contributions include synthetic reproduction fixtures, protocol compatibility fixes and clearer diagnostics. Explain the trigger, expected behavior and validation. Add a regression test for behavior fixes and run:

```bash
python3 -m unittest discover -s tests -p test_mcp_health_check.py -v
python3 examples/webhook_signature_fixture.py
```

Do not include credentials, private endpoints, production logs or customer data. Do not call production tools or introduce spending as part of a test. Discuss a new transport or protocol lifecycle before implementing it; the current scope is documented in the quick start.
