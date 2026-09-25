import argparse
import json
import os
import re
import sys

from opengateway_sandbox_sdk import Simswap


E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def require_credentials() -> tuple[str, str]:
    client_id = os.getenv("OPEN_GATEWAY_CLIENT_ID")
    client_secret = os.getenv("OPEN_GATEWAY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Open Gateway credentials. Set OPEN_GATEWAY_CLIENT_ID "
            "and OPEN_GATEWAY_CLIENT_SECRET."
        )
    return client_id, client_secret


def validate_phone_number(value: str) -> str:
    if not E164_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "Phone number must use E.164 format, for example +5491123456789."
        )
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Defensive SIM-swap check using the Open Gateway SIM Swap API."
    )
    parser.add_argument("phone_number", type=validate_phone_number)
    parser.add_argument(
        "max_age",
        nargs="?",
        type=int,
        default=2400,
        help="Look-back window in hours (default: 2400 = 100 days).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Print a machine-readable JSON result.",
    )
    args = parser.parse_args()
    if args.max_age <= 0:
        parser.error("max_age must be greater than 0")
    return args


def main() -> int:
    args = parse_args()

    try:
        client_id, client_secret = require_credentials()
        simswap_client = Simswap(
            client_id,
            client_secret,
            args.phone_number,
        )

        recent_swap = simswap_client.check(max_age=args.max_age)
        last_swap = simswap_client.retrieve_date()

        result = {
            "phone_number": args.phone_number,
            "max_age_hours": args.max_age,
            "recent_swap": bool(recent_swap),
            "last_swap": last_swap,
            "source": "Open Gateway SIM Swap API",
            "interpretation": (
                "A SIM change was reported inside the requested window."
                if recent_swap
                else "No SIM change was reported inside the requested window."
            ),
        }

        if args.as_json:
            print(json.dumps(result, default=str, ensure_ascii=False, indent=2))
        else:
            print(f"Phone: {result['phone_number']}")
            print(f"Look-back window: {result['max_age_hours']} hours")
            print(f"Recent SIM change: {result['recent_swap']}")
            print(f"Last SIM change: {result['last_swap']}")
            print(result["interpretation"])

        return 0
    except Exception as exc:
        error = {
            "ok": False,
            "error": str(exc),
            "source": "Open Gateway SIM Swap API",
        }
        if args.as_json:
            print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
