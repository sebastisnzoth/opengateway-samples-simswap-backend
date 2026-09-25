# SIM Swap defensive checker

This repository is a defensive sample for checking whether a phone line had a recent SIM change through the Open Gateway SIM Swap API.

It is based on the Telefónica Open Gateway sample and is intended for fraud detection, incident response, and testing with numbers you own or are authorized to verify.

## What it does

The project provides:

- a Python CLI that checks whether a SIM change happened inside a requested time window;
- retrieval of the last reported SIM-change date;
- optional JSON output for evidence collection or integration;
- a small Flask API exposing the same defensive checks.

A positive result means the network reports a SIM change. It does **not** by itself prove fraud: legitimate SIM replacements, eSIM migrations, or carrier operations can also produce a SIM-change event.

## Important limitation

The Telefónica Sandbox is a testing environment. Sandbox results are not forensic evidence for a real mobile line.

Real carrier availability depends on the Open Gateway provider and country. For an incident involving an Argentine number, confirm whether the relevant Argentine operator exposes the SIM Swap API for that line. Carrier records remain the authoritative source for a suspected fraudulent replacement or port-out.

## Requirements

- Python 3.9+
- Open Gateway / Telefónica Sandbox credentials
- Git, if cloning the repository

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Credentials are no longer stored in the source code.

Set them as environment variables:

```bash
export OPEN_GATEWAY_CLIENT_ID="your-client-id"
export OPEN_GATEWAY_CLIENT_SECRET="your-client-secret"
```

Optional server configuration:

```bash
export PORT=8000
```

See `.env.example` for the expected variables. Do not commit real credentials.

## CLI usage

Phone numbers must use E.164 format, including the leading `+`.

Check the default 2400-hour / 100-day window:

```bash
python command/simswap-sdk.py +5491123456789
```

Check a custom look-back window, for example 720 hours / 30 days:

```bash
python command/simswap-sdk.py +5491123456789 720
```

Machine-readable output:

```bash
python command/simswap-sdk.py +5491123456789 720 --json
```

Example JSON shape:

```json
{
  "phone_number": "+5491123456789",
  "max_age_hours": 720,
  "recent_swap": false,
  "last_swap": "provider-dependent timestamp",
  "source": "Open Gateway SIM Swap API",
  "interpretation": "No SIM change was reported inside the requested window."
}
```

The CLI now passes the user-supplied `max_age` value to the API. The previous sample always checked 2400 hours even when another value was provided.

## Flask server

Run:

```bash
python server/simswap-server.py
```

Health check:

```bash
curl http://localhost:8000/health
```

Check for a recent SIM change:

```bash
curl 'http://localhost:8000/check/+5491123456789/720'
```

Retrieve the last reported SIM-change date:

```bash
curl 'http://localhost:8000/retrieve_date/+5491123456789'
```

## Interpreting results during an incident

If the API reports a change near the time your phone unexpectedly lost mobile service, preserve the output together with:

- the exact date and time the phone lost network service;
- carrier SMS or email notifications;
- account recovery notifications;
- suspicious login timestamps;
- the carrier incident or complaint number.

Ask the carrier to confirm whether the event was a physical SIM replacement, eSIM issuance, or port-out, and to preserve the associated account records.

## Security

Do not expose this sample server directly to the public Internet without authentication, rate limiting, restricted CORS, logging controls, and appropriate authorization for every queried phone number.

Never publish `OPEN_GATEWAY_CLIENT_SECRET` or commit it to Git.

## Upstream references

- Telefónica Open Gateway SIM Swap sample: https://github.com/Telefonica/opengateway-samples-simswap
- CAMARA Project: https://camaraproject.org
