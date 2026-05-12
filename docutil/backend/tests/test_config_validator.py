"""
트랙 #65 — ENCRYPTION_KEY validator 강화 단위 테스트.

`app.core.config.Settings.encryption_key` validator 가:
- 강한 random hex 키는 통과시키고,
- 약한 패턴화 키(데모 키, 반복 패턴, 저엔트로피)는 거부하는지 검증.

목적: 트랙 #64 회전 사고(데모 키가 운영에 적재됨) 재발을 코드 레이어에서
차단했음을 회귀 테스트로 고정.
"""

from __future__ import annotations

import secrets

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _make_settings(encryption_key: str) -> Settings:
    """ENCRYPTION_KEY 만 override 한 Settings 인스턴스 생성.

    conftest.py 가 다른 필수 환경변수를 미리 주입하므로, 여기서는
    encryption_key 하나만 검증 대상으로 삼는다.
    """
    return Settings(encryption_key=encryption_key)


# ---------------------------------------------------------------------------
# 통과 케이스 — 강한 random hex
# ---------------------------------------------------------------------------
def test_encryption_key_strong_token_hex_passes() -> None:
    """secrets.token_hex(32) 가 생성한 강한 키는 통과한다."""
    key = secrets.token_hex(32)
    settings = _make_settings(key)
    assert settings.encryption_key == key


def test_encryption_key_multiple_random_keys_pass() -> None:
    """여러 차례 생성한 random 키 모두 통과 — false-negative 없음 확인."""
    for _ in range(10):
        key = secrets.token_hex(32)
        settings = _make_settings(key)
        assert settings.encryption_key == key


# ---------------------------------------------------------------------------
# 거부 케이스 — 형식 위반
# ---------------------------------------------------------------------------
def test_encryption_key_invalid_hex_rejected() -> None:
    """hex 가 아닌 문자가 섞이면 거부."""
    with pytest.raises(ValidationError, match="valid hex"):
        _make_settings("g" * 64)


def test_encryption_key_wrong_length_short_rejected() -> None:
    """32바이트 미만(예: 16바이트=32자)은 거부."""
    with pytest.raises(ValidationError, match="32 bytes"):
        _make_settings("0" * 32)


def test_encryption_key_wrong_length_long_rejected() -> None:
    """32바이트 초과는 거부."""
    with pytest.raises(ValidationError, match="32 bytes"):
        _make_settings("a" * 128)


# ---------------------------------------------------------------------------
# 거부 케이스 — 반복 패턴 (트랙 #64 데모 키 시나리오)
# ---------------------------------------------------------------------------
def test_encryption_key_demo_pattern_16char_repeat_rejected() -> None:
    """`0123456789abcdef` × 4 — 트랙 #64 실제 사고 데모 키 패턴."""
    weak_key = "0123456789abcdef" * 4  # 64자
    with pytest.raises(ValidationError, match="repeating 16-char"):
        _make_settings(weak_key)


def test_encryption_key_32char_repeat_rejected() -> None:
    """32자 hex 가 2회 반복되는 패턴 거부."""
    half = secrets.token_hex(16)  # 32자 random
    weak_key = half + half  # 64자, 2회 반복
    with pytest.raises(ValidationError, match="repeating 32-char"):
        _make_settings(weak_key)


# ---------------------------------------------------------------------------
# 거부 케이스 — distinct byte 부족 (저엔트로피)
# ---------------------------------------------------------------------------
def test_encryption_key_single_byte_repeated_rejected() -> None:
    """한 바이트(`aa`)가 32회 반복 — distinct=1.

    `aa` × 32 는 16자 반복 패턴(`aaaaaaaaaaaaaaaa` × 4)에 먼저 매칭되므로
    검증 순서에 따라 'repeating 16-char' 메시지로 차단된다. 어떤 메시지든
    ValidationError 발생 자체가 핵심.
    """
    with pytest.raises(ValidationError):
        _make_settings("aa" * 32)


def test_encryption_key_low_distinct_bytes_rejected() -> None:
    """distinct byte 가 16개 미만인 키 거부.

    8개 distinct byte 가 4회 반복: `00 11 22 33 44 55 66 77` × 4 = distinct 8.
    """
    pattern = "0011223344556677"  # 8 distinct bytes, 16 chars
    weak_key = pattern * 4  # 32 bytes, 64 chars
    # 이 키는 32자 반복 패턴이 아니지만 16자 반복 → 16자 반복 차단에 먼저 걸린다.
    # distinct 검사를 별도로 확인하려면 비반복 저-distinct 키 필요.
    with pytest.raises(ValidationError):
        _make_settings(weak_key)


def test_encryption_key_non_repeating_low_distinct_rejected() -> None:
    """반복 패턴은 아니지만 distinct byte 가 16 미만인 키.

    8 distinct byte 를 무작위 순서로 배치 → 반복 패턴 검사는 통과,
    distinct 검사에서 차단된다.
    """
    # 8 distinct bytes 를 32회 채우되 반복 패턴 회피
    bytes_pool = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]
    rng = secrets.SystemRandom()
    # 16/32/48 자 경계가 모두 같아지는 패턴을 피하기 위해 셔플 반복
    while True:
        sequence = [rng.choice(bytes_pool) for _ in range(32)]
        key = bytes(sequence).hex()
        # 반복 패턴 검사를 우연히 통과하는지 확인 후 사용
        quad_repeat = key[:16] == key[16:32] == key[32:48] == key[48:64]
        half_repeat = key[:32] == key[32:64]
        if not quad_repeat and not half_repeat:
            break
    with pytest.raises(ValidationError, match="distinct bytes"):
        _make_settings(key)


# ---------------------------------------------------------------------------
# 거부 케이스 — Shannon entropy 부족
# ---------------------------------------------------------------------------
def test_encryption_key_low_entropy_rejected() -> None:
    """엔트로피가 4.5 bits/byte 미만인 키 거부.

    distinct 가 정확히 16 이지만 분포가 매우 편향된 키를 만든다:
    한 바이트(0x00) 가 17회 + 나머지 15 byte 가 1회씩 = distinct 16, 저엔트로피.
    distinct 조건은 통과, entropy 조건에서 차단됨.
    """
    # 32 바이트 중 17개를 0x00, 나머지 15개를 0x01~0x0f 로
    sequence = [0x00] * 17 + list(range(1, 16))  # len = 32, distinct = 16
    # 셔플하여 반복 패턴 회피
    rng = secrets.SystemRandom()
    while True:
        rng.shuffle(sequence)
        key = bytes(sequence).hex()
        quad_repeat = key[:16] == key[16:32] == key[32:48] == key[48:64]
        half_repeat = key[:32] == key[32:64]
        if not quad_repeat and not half_repeat:
            break

    with pytest.raises(ValidationError, match="entropy"):
        _make_settings(key)


# ---------------------------------------------------------------------------
# 메시지 가이드 — 사용자에게 강한 키 생성 명령어 안내
# ---------------------------------------------------------------------------
def test_encryption_key_error_message_includes_token_hex_hint() -> None:
    """약한 키 에러 메시지에 `secrets.token_hex(32)` 명령어 힌트 포함 확인."""
    weak_key = "0123456789abcdef" * 4
    with pytest.raises(ValidationError) as excinfo:
        _make_settings(weak_key)
    assert "secrets.token_hex(32)" in str(excinfo.value)


# ---------------------------------------------------------------------------
# 트랙 #67 — DB_SCHEMA validator 단위 테스트
# ---------------------------------------------------------------------------
# `app.core.config.Settings.db_schema` validator 가 시나리오 D (DB_SCHEMA env
# 누락/오타/`public` 주입) 를 차단하는지 검증. Phase 4.1 ADR-5 스키마 격리
# 원칙 보호 회귀 테스트.
class TestDbSchemaValidator:
    """DB_SCHEMA validator — 시나리오 D 차단."""

    # ── 통과 케이스 ──────────────────────────────────────────────────────
    def test_strong_schema_passes(self) -> None:
        """기본값 `document_utilization` 통과."""
        s = Settings(db_schema="document_utilization", encryption_key=secrets.token_hex(32))
        assert s.db_schema == "document_utilization"

    def test_underscore_first_allowed(self) -> None:
        """첫 글자가 언더스코어인 식별자 허용 (PG 표준)."""
        s = Settings(db_schema="_test_schema", encryption_key=secrets.token_hex(32))
        assert s.db_schema == "_test_schema"

    def test_max_length_63_allowed(self) -> None:
        """PG NAMEDATALEN 한계인 63자까지 허용."""
        name = "a" * 63
        s = Settings(db_schema=name, encryption_key=secrets.token_hex(32))
        assert s.db_schema == name

    # ── 거부 케이스 — 빈 값 / 공백 ───────────────────────────────────────
    def test_empty_rejected(self) -> None:
        """빈 문자열 거부."""
        with pytest.raises(ValidationError, match="non-empty"):
            Settings(db_schema="", encryption_key=secrets.token_hex(32))

    def test_whitespace_only_rejected(self) -> None:
        """공백 only 거부 (validator 가 strip 후 빈 값으로 판단)."""
        with pytest.raises(ValidationError, match="non-empty"):
            Settings(db_schema="   ", encryption_key=secrets.token_hex(32))

    # ── 거부 케이스 — public schema 차단 ─────────────────────────────────
    def test_public_rejected(self) -> None:
        """`public` 거부 — ADR-5 격리 원칙 위반."""
        with pytest.raises(ValidationError, match="must not be 'public'"):
            Settings(db_schema="public", encryption_key=secrets.token_hex(32))

    def test_public_case_insensitive(self) -> None:
        """대문자 `PUBLIC` 도 거부 — 대소문자 무시."""
        with pytest.raises(ValidationError, match="must not be 'public'"):
            Settings(db_schema="PUBLIC", encryption_key=secrets.token_hex(32))

    # ── 거부 케이스 — 식별자 규칙 위반 ────────────────────────────────────
    def test_invalid_chars_rejected(self) -> None:
        """`-` 등 PG 식별자에 허용되지 않는 문자 거부."""
        with pytest.raises(ValidationError, match="valid PostgreSQL identifier"):
            Settings(db_schema="my-schema", encryption_key=secrets.token_hex(32))

    def test_starts_with_digit_rejected(self) -> None:
        """숫자로 시작하는 식별자 거부."""
        with pytest.raises(ValidationError, match="valid PostgreSQL identifier"):
            Settings(db_schema="9schema", encryption_key=secrets.token_hex(32))

    def test_too_long_rejected(self) -> None:
        """64자 이상 거부 (PG NAMEDATALEN 초과)."""
        with pytest.raises(ValidationError, match="valid PostgreSQL identifier"):
            Settings(db_schema="a" * 64, encryption_key=secrets.token_hex(32))
