from __future__ import annotations

from typing import Protocol, runtime_checkable

_SENT: list[tuple[str, str]] = []


@runtime_checkable
class SmsProvider(Protocol):
    def send(self, phone: str, body: str) -> None: ...


class ConsoleSmsProvider:
    """Development provider: prints the message. OTP codes appear in backend logs."""

    def send(self, phone: str, body: str) -> None:
        _SENT.append((phone, body))
        print(f"[YAVAR SMS] to={phone} body={body}", flush=True)


class MemorySmsProvider:
    """Test double that records sent messages (shared with console in-process)."""

    @property
    def messages(self) -> list[tuple[str, str]]:
        return _SENT

    def send(self, phone: str, body: str) -> None:
        _SENT.append((phone, body))
        print(f"[YAVAR SMS] to={phone} body={body}", flush=True)

    def last_code_for(self, phone: str) -> str | None:
        for dest, body in reversed(_SENT):
            if dest != phone:
                continue
            parts = body.replace(":", " ").split()
            for token in reversed(parts):
                if token.isdigit() and len(token) >= 4:
                    return token
        return None

    def clear(self) -> None:
        _SENT.clear()
