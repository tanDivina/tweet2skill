"""
Upstash Redis REST client using only Python stdlib.

All operations go through the Upstash REST API with Bearer-token auth.
No SDK required — just urllib and json.
"""

import json
import os
import urllib.request
import urllib.error


def _rest_url():
    val = os.environ.get("UPSTASH_REDIS_REST_URL", "")
    # Robustly strip quotes, whitespace, and literal escape newlines (\n)
    val = val.strip('"').strip("'").strip()
    if val.endswith("\\n"):
        val = val[:-2].strip()
    return val


def _rest_token():
    val = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")
    # Robustly strip quotes, whitespace, and literal escape newlines (\n)
    val = val.strip('"').strip("'").strip()
    if val.endswith("\\n"):
        val = val[:-2].strip()
    return val


def _execute(command_parts):
    """Execute a single Redis command via the Upstash REST API.

    Args:
        command_parts: list of strings, e.g. ["SET", "key", "value"]

    Returns:
        The "result" field from the Upstash response.

    Raises:
        Exception on HTTP or Redis errors.
    """
    url = _rest_url()
    token = _rest_token()

    if not url or not token:
        raise RuntimeError("Upstash Redis credentials are not configured.")

    endpoint = url.rstrip("/")
    payload = json.dumps(command_parts).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if "error" in body and body["error"]:
                raise RuntimeError(f"Upstash error: {body['error']}")
            return body.get("result")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Upstash HTTP {exc.code}: {error_body}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Upstash connection error: {exc}") from exc


def _pipeline(commands):
    """Execute multiple Redis commands in a single pipeline request.

    Args:
        commands: list of command lists, e.g. [["INCR", "k"], ["EXPIRE", "k", "60"]]

    Returns:
        List of result objects (one per command).
    """
    url = _rest_url()
    token = _rest_token()

    if not url or not token:
        raise RuntimeError("Upstash Redis credentials are not configured.")

    endpoint = url.rstrip("/") + "/pipeline"
    payload = json.dumps(commands).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body  # list of {result: ...} objects
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Upstash pipeline HTTP {exc.code}: {error_body}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Upstash pipeline connection error: {exc}") from exc


# ── Convenience wrappers ────────────────────────────────────────────

def get(key):
    """GET a key. Returns the string value or None."""
    return _execute(["GET", key])


def set(key, value, ex=None):
    """SET a key. Optional `ex` sets TTL in seconds."""
    if ex is not None:
        return _execute(["SET", key, str(value), "EX", str(int(ex))])
    return _execute(["SET", key, str(value)])


def incr(key):
    """INCR a key (atomic integer increment). Returns new value as int."""
    result = _execute(["INCR", key])
    return int(result) if result is not None else 1


def expire(key, seconds):
    """Set a TTL on an existing key."""
    return _execute(["EXPIRE", key, str(int(seconds))])


def ttl(key):
    """Get the remaining TTL of a key in seconds. Returns -1/-2 per Redis semantics."""
    result = _execute(["TTL", key])
    return int(result) if result is not None else -2


def hset(key, field, value):
    """HSET a hash field."""
    return _execute(["HSET", key, field, str(value)])


def hget(key, field):
    """HGET a hash field. Returns string or None."""
    return _execute(["HGET", key, field])


def hgetall(key):
    """HGETALL – returns a dict of {field: value}."""
    raw = _execute(["HGETALL", key])
    if not raw:
        return {}
    # Upstash returns a flat list: [field1, val1, field2, val2, ...]
    it = iter(raw)
    return dict(zip(it, it))


def delete(key):
    """DEL a key."""
    return _execute(["DEL", key])


def incr_with_ttl(key, ttl_seconds):
    """Atomically INCR a key and set TTL only if the key is new (pipeline).

    Returns the new counter value as int.
    """
    results = _pipeline([
        ["INCR", key],
        ["TTL", key],
    ])
    counter = int(results[0].get("result", 1))
    current_ttl = int(results[1].get("result", -1))

    # Only set TTL if the key has no expiry yet (-1 = no TTL, -2 = key gone)
    if current_ttl == -1:
        _execute(["EXPIRE", key, str(int(ttl_seconds))])

    return counter


def rpush(key, value):
    """RPUSH a value onto a list."""
    return _execute(["RPUSH", key, str(value)])


def hdel(key, field):
    """HDEL a hash field."""
    return _execute(["HDEL", key, field])


def hincrby(key, field, increment):
    """HINCRBY a hash field atomically. Returns the new value as int."""
    result = _execute(["HINCRBY", key, field, str(int(increment))])
    return int(result) if result is not None else 0


