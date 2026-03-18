"""Timezone helper – ใช้เวลาไทย (Asia/Bangkok, UTC+7) ทั่วทั้งระบบ"""

from datetime import datetime, timezone, timedelta

TH_TZ = timezone(timedelta(hours=7))  # UTC+7


def now_th() -> datetime:
    """Return current Thai local time (naive datetime – ไม่มี tzinfo เพื่อให้เข้ากับ DB column ที่เป็น DateTime ธรรมดา)"""
    return datetime.now(TH_TZ).replace(tzinfo=None)
