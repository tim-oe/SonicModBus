"""Tests for LocalToUTCDateTime TypeDecorator.

Verifies that the persistence layer correctly translates between naive
local (America/Chicago) datetimes and naive UTC datetimes without any
UTC knowledge leaking into the application layer.
"""

from datetime import datetime

import pytest

from sonic_persistence.types import LocalToUTCDateTime

# America/Chicago offsets:
#   CDT (summer, UTC-5): 10:00 local -> 15:00 UTC
#   CST (winter, UTC-6): 10:00 local -> 16:00 UTC
CDT_LOCAL = datetime(2026, 7, 15, 10, 0, 0)
CDT_UTC = datetime(2026, 7, 15, 15, 0, 0)

CST_LOCAL = datetime(2026, 1, 15, 10, 0, 0)
CST_UTC = datetime(2026, 1, 15, 16, 0, 0)

# DST fall-back: 2026-11-01 01:30 is ambiguous (CDT or CST).
# is_dst=False -> picks CST (UTC-6) -> UTC 07:30
DST_FALLBACK_LOCAL = datetime(2026, 11, 1, 1, 30, 0)
DST_FALLBACK_UTC = datetime(2026, 11, 1, 7, 30, 0)


@pytest.fixture
def typ() -> LocalToUTCDateTime:
    return LocalToUTCDateTime()


# ---------------------------------------------------------------------------
# process_bind_param  (write path: local -> UTC)
# ---------------------------------------------------------------------------


class TestBindParam:
    def test_cdt_converts_to_utc(self, typ):
        assert typ.process_bind_param(CDT_LOCAL, None) == CDT_UTC

    def test_cst_converts_to_utc(self, typ):
        assert typ.process_bind_param(CST_LOCAL, None) == CST_UTC

    def test_microseconds_preserved(self, typ):
        local = datetime(2026, 7, 15, 10, 30, 45, 123456)
        result = typ.process_bind_param(local, None)
        assert result == datetime(2026, 7, 15, 15, 30, 45, 123456)

    def test_result_is_naive(self, typ):
        result = typ.process_bind_param(CDT_LOCAL, None)
        assert result.tzinfo is None

    def test_none_returns_none(self, typ):
        assert typ.process_bind_param(None, None) is None

    def test_dst_fallback_picks_cst(self, typ):
        """Ambiguous fall-back hour: is_dst=False picks standard time (CST, UTC-6)."""
        assert typ.process_bind_param(DST_FALLBACK_LOCAL, None) == DST_FALLBACK_UTC

    def test_cdt_offset_is_minus_5(self, typ):
        utc = typ.process_bind_param(CDT_LOCAL, None)
        offset_hours = int((utc - CDT_LOCAL).total_seconds() // 3600)
        assert offset_hours == 5, "CDT should be UTC-5"

    def test_cst_offset_is_minus_6(self, typ):
        utc = typ.process_bind_param(CST_LOCAL, None)
        offset_hours = int((utc - CST_LOCAL).total_seconds() // 3600)
        assert offset_hours == 6, "CST should be UTC-6"


# ---------------------------------------------------------------------------
# process_result_value  (read path: UTC -> local)
# ---------------------------------------------------------------------------


class TestResultValue:
    def test_cdt_converts_to_local(self, typ):
        assert typ.process_result_value(CDT_UTC, None) == CDT_LOCAL

    def test_cst_converts_to_local(self, typ):
        assert typ.process_result_value(CST_UTC, None) == CST_LOCAL

    def test_microseconds_preserved(self, typ):
        utc = datetime(2026, 7, 15, 15, 30, 45, 123456)
        result = typ.process_result_value(utc, None)
        assert result == datetime(2026, 7, 15, 10, 30, 45, 123456)

    def test_result_is_naive(self, typ):
        result = typ.process_result_value(CDT_UTC, None)
        assert result.tzinfo is None

    def test_none_returns_none(self, typ):
        assert typ.process_result_value(None, None) is None


# ---------------------------------------------------------------------------
# Round-trip  (write then read must return the original local value)
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_cdt(self, typ):
        utc = typ.process_bind_param(CDT_LOCAL, None)
        assert typ.process_result_value(utc, None) == CDT_LOCAL

    def test_cst(self, typ):
        utc = typ.process_bind_param(CST_LOCAL, None)
        assert typ.process_result_value(utc, None) == CST_LOCAL

    def test_microseconds(self, typ):
        local = datetime(2026, 7, 15, 10, 30, 45, 123456)
        utc = typ.process_bind_param(local, None)
        assert typ.process_result_value(utc, None) == local

    def test_dst_fallback(self, typ):
        """Fall-back ambiguous time round-trips correctly (CST interpretation)."""
        utc = typ.process_bind_param(DST_FALLBACK_LOCAL, None)
        assert typ.process_result_value(utc, None) == DST_FALLBACK_LOCAL
