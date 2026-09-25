import os
import re

from flask import Flask, jsonify
from flask_cors import CORS
from opengateway_sandbox_sdk import Simswap


app = Flask(__name__)
CORS(app)

PORT = int(os.getenv("PORT", "8000"))
E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def get_credentials() -> tuple[str, str]:
    client_id = os.getenv("OPEN_GATEWAY_CLIENT_ID")
    client_secret = os.getenv("OPEN_GATEWAY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Open Gateway credentials. Set OPEN_GATEWAY_CLIENT_ID "
            "and OPEN_GATEWAY_CLIENT_SECRET."
        )
    return client_id, client_secret


def get_client(phone_number: str) -> Simswap:
    if not E164_RE.fullmatch(phone_number):
        raise ValueError(
            "Phone number must use E.164 format, for example +5491123456789."
        )
    client_id, client_secret = get_credentials()
    return Simswap(client_id, client_secret, phone_number)


@app.get("/health")
def health():
    configured = bool(
        os.getenv("OPEN_GATEWAY_CLIENT_ID")
        and os.getenv("OPEN_GATEWAY_CLIENT_SECRET")
    )
    return jsonify(
        ok=True,
        configured=configured,
        service="defensive-simswap-check",
    )


@app.get("/retrieve_date/<string:phone_number>")
def sdk_retrieve_date(phone_number: str):
    try:
        simswap_client = get_client(phone_number)
        last_swap = simswap_client.retrieve_date()
        return jsonify(
            ok=True,
            phone_number=phone_number,
            last_swap=last_swap,
            source="Open Gateway SIM Swap API",
        )
    except (ValueError, RuntimeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    except Exception as exc:
        app.logger.exception("SIM swap retrieve_date failed")
        return jsonify(ok=False, error=str(exc)), 502


@app.get("/check/<string:phone_number>/<int:max_age>")
def sdk_check(phone_number: str, max_age: int):
    if max_age <= 0:
        return jsonify(ok=False, error="max_age must be greater than 0"), 400

    try:
        simswap_client = get_client(phone_number)
        recent_swap = bool(simswap_client.check(max_age=max_age))
        return jsonify(
            ok=True,
            phone_number=phone_number,
            max_age_hours=max_age,
            recent_swap=recent_swap,
            source="Open Gateway SIM Swap API",
            interpretation=(
                "A SIM change was reported inside the requested window."
                if recent_swap
                else "No SIM change was reported inside the requested window."
            ),
        )
    except (ValueError, RuntimeError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    except Exception as exc:
        app.logger.exception("SIM swap check failed")
        return jsonify(ok=False, error=str(exc)), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
