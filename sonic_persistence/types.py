"""SQLAlchemy custom column types for sonic_persistence."""

from datetime import datetime

import pytz
import tzlocal
from sqlalchemy import DateTime, types

__all__ = ["LocalToUTCDateTime"]


class LocalToUTCDateTime(types.TypeDecorator):
    """SQLAlchemy type for DATETIME columns that store UTC.

    On write: treats the incoming naive datetime as local timezone
              (America/Chicago on this system) and converts it to
              naive UTC before sending to the database.
    On read:  converts the stored naive UTC value back to naive local time.

    This centralises the local->UTC conversion in the persistence layer
    so the rest of the application can work with naive local datetimes
    without any UTC awareness.

    is_dst=False is used for DST fall-back ambiguous times (picks the
    standard/non-DST interpretation), avoiding AmbiguousTimeError for
    the small number of readings that land in that window.
    """

    impl = DateTime
    cache_ok = True

    _local_tz = pytz.timezone(tzlocal.get_localzone_name())

    def process_bind_param(self, value: datetime, dialect):
        if value is None:
            return None
        local_dt = self._local_tz.localize(value, is_dst=False)
        return local_dt.astimezone(pytz.utc).replace(tzinfo=None)

    def process_result_value(self, value: datetime, dialect):
        if value is None:
            return None
        utc_dt = pytz.utc.localize(value)
        return utc_dt.astimezone(self._local_tz).replace(tzinfo=None)
