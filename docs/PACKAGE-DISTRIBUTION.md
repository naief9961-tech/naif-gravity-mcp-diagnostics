# NAIF Gravity MCP Doctor — package distribution

**Status:** both package registries have a live 0.3.0 release; version 0.3.1 updates search-facing descriptions and documentation without changing diagnostic behavior. Verify the latest release at:
- https://pypi.org/project/naif-gravity-mcp-doctor/
- https://www.npmjs.com/package/naif-gravity-mcp-doctor

The package reuses the existing free, local **NAIF Error Passport** (MIT). It never automatically uploads reports, executes MCP tools, charges a buyer or contacts the store. It is limited to bounded MCP discovery; it does not guarantee repair or conformance.

## Install from the official registries

```bash
python3 -m pip install naif-gravity-mcp-doctor
npm install -g naif-gravity-mcp-doctor
```

Both commands provide `naif-mcp-doctor`. **The npm package requires Python 3.10+ on PATH**, since its dependency-free Node.js launcher calls the same audited Python script, rather than a divergent implementation. Node.js 20+ is required for the npm launcher.

## Local offline use

```bash
naif-mcp-doctor --report sanitized-report.json --format markdown
naif-mcp-doctor --report - --format json < sanitized-report.json
```

Only an explicitly authorized owner endpoint can be probed, with `--probe https://authorized.example/mcp --authorized`. Even then the tool checks initialize/tools/list, never tools/call or payment. Do not share credentials, personal data, raw server bodies or secret-bearing URLs.

## Build and audit before upload

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -q
npm test
npm pack --dry-run
python3 -m pip install build
python3 -m build --sdist --wheel .
```

Verify archive contents and SHA-256 before publishing. Registry distributions are immutable. The same Python implementation powers the existing source/Action, npm launcher and Python entry point; there are no npm install hooks or runtime dependencies.

## PyPI: no long-lived tokens

Configure a **pending** trusted publisher in your real PyPI account if the project is not yet claimed. Project name `naif-gravity-mcp-doctor`; GitHub owner `naief9961-tech`; repo `naif-gravity-mcp-diagnostics`; workflow filename `package-distribution.yml`, environment `pypi`. Configure the GitHub environment for owner approval and use a reviewed release tag before manually selecting `publish_pypi=true`. A pending PyPI publisher does not reserve the name. Official setup: https://docs.pypi.org/trusted-publishers/

## npm publishing

The initial npm package was published through npm staged publishing and account-owner approval. Subsequent releases also require the current account publishing rules. Use the same GitHub owner/repo and workflow filename `package-distribution.yml`, environment `npm`, and npm CLI 11.5.1+ under Node 24 in CI. After trusted publishing and any first-upload step required by npm, publish only from a reviewed tag by manually selecting `publish_npm=true`. Never place tokens in source, logs or chat. Official setup: https://docs.npmjs.com/trusted-publishers/

## GitHub Action

The repository already has a composite `action.yml` and versioned public releases. GitHub Marketplace publication requires its separate publisher agreement/review. A GitHub release is not evidence of PyPI, npm or Marketplace publication. No traffic or ranking improvement is guaranteed; deps.dev and Libraries.io choose their own indexing schedules.

## Release safeguards

- CI builds/tests by default; publishing requires a manual workflow dispatch on a version tag and preconfigured trusted publisher.
- The two registries are independent; never infer one publication from the other.
- Do not install third-party publishers, unlock authentication, introduce install hooks, scrape private data, auto-generate SEO spam, or modify production payment and agent routes.
- No public customer/probe uploads, no unsolicited outreach, no stealth telemetry.
