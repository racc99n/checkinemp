import logging
import asyncio
import threading
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_bot = None
_admin_chat_id: Optional[str] = None
_bot_token: Optional[str] = None


def init_telegram(token: str, admin_chat_id: str):
    global _bot, _admin_chat_id, _bot_token
    if not token:
        logger.warning("Telegram bot token not configured - notifications disabled")
        return
    try:
        from telegram import Bot
        _bot = Bot(token=token)
        _bot_token = token
        _admin_chat_id = admin_chat_id
        logger.info(f"Telegram bot initialized (chat_id: {admin_chat_id})")
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")


async def _send_message(chat_id: str, text: str, photo_b64: Optional[str] = None):
    """ส่งข้อความผ่าน Telegram Bot API"""
    if not _bot_token or not chat_id:
        return
    try:
        from telegram import Bot
        bot = Bot(token=_bot_token)
        if photo_b64:
            import base64
            import io
            if "," in photo_b64:
                photo_b64 = photo_b64.split(",")[1]
            photo_bytes = base64.b64decode(photo_b64)
            await bot.send_photo(
                chat_id=chat_id,
                photo=io.BytesIO(photo_bytes),
                caption=text,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Telegram send error to {chat_id}: {e}")


def _fire(coro):
    """รัน async coroutine จาก sync context อย่างปลอดภัย"""
    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Telegram _fire error: {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def notify_check_in(
    employee_name: str,
    employee_code: str,
    device_name: str,
    timestamp: datetime,
    status: str,
    employee_chat_id: Optional[str] = None,
    confidence: float = 0.0
):
    time_str = timestamp.strftime("%H:%M:%S")
    date_str = timestamp.strftime("%d/%m/%Y")
    status_icon = "🟡 สาย" if status == "late" else "🟢 ตรงเวลา"

    admin_msg = (
        f"📥 <b>เข้างาน</b>\n"
        f"👤 {employee_name} ({employee_code})\n"
        f"🕐 {time_str} น. | {date_str}\n"
        f"📍 {device_name}\n"
        f"📊 {status_icon} | ความแม่นยำ: {confidence:.1f}%"
    )

    employee_msg = (
        f"✅ ระบบบันทึกการเข้างานของคุณแล้ว\n"
        f"🕐 เวลา: {time_str} น.\n"
        f"📅 วันที่: {date_str}\n"
        f"สถานะ: {status_icon}"
    )

    if _admin_chat_id:
        _fire(_send_message(_admin_chat_id, admin_msg))
    if employee_chat_id:
        _fire(_send_message(employee_chat_id, employee_msg))


def notify_check_out(
    employee_name: str,
    employee_code: str,
    device_name: str,
    check_in_at: datetime,
    check_out_at: datetime,
    employee_chat_id: Optional[str] = None
):
    duration = check_out_at - check_in_at
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    time_str = check_out_at.strftime("%H:%M:%S")
    date_str = check_out_at.strftime("%d/%m/%Y")

    admin_msg = (
        f"📤 <b>ออกงาน</b>\n"
        f"👤 {employee_name} ({employee_code})\n"
        f"🕐 {time_str} น. | {date_str}\n"
        f"📍 {device_name}\n"
        f"⏱ ทำงาน: {hours} ชม. {minutes} นาที"
    )

    employee_msg = (
        f"👋 ระบบบันทึกการออกงานของคุณแล้ว\n"
        f"🕐 เวลา: {time_str} น.\n"
        f"⏱ ทำงานทั้งหมด: {hours} ชม. {minutes} นาที"
    )

    if _admin_chat_id:
        _fire(_send_message(_admin_chat_id, admin_msg))
    if employee_chat_id:
        _fire(_send_message(employee_chat_id, employee_msg))


def notify_unknown_face(device_name: str, timestamp: datetime, photo_b64: Optional[str] = None):
    time_str = timestamp.strftime("%H:%M:%S")
    date_str = timestamp.strftime("%d/%m/%Y")
    msg = (
        f"⚠️ <b>ตรวจพบใบหน้าที่ไม่รู้จัก</b>\n"
        f"📍 {device_name}\n"
        f"🕐 {time_str} น. | {date_str}\n"
        f"กรุณาตรวจสอบ"
    )
    if _admin_chat_id:
        _fire(_send_message(_admin_chat_id, msg))


def notify_blocked_device(fingerprint_hash: str, timestamp: datetime):
    time_str = timestamp.strftime("%H:%M:%S")
    msg = (
        f"🚫 <b>อุปกรณ์ไม่ได้รับอนุญาต</b>\n"
        f"🕐 {time_str} น.\n"
        f"Fingerprint: <code>{fingerprint_hash[:16]}...</code>"
    )
    if _admin_chat_id:
        _fire(_send_message(_admin_chat_id, msg))
