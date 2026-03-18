# ระบบสแกนหน้าเข้างาน (Face Attendance System)

ระบบบันทึกเวลาเข้า-ออกงานด้วยการสแกนใบหน้าผ่านโทรศัพท์ พร้อมแจ้งเตือนผ่าน Telegram Bot

## ฟีเจอร์หลัก

- 📷 **สแกนใบหน้า** ผ่าน browser ของโทรศัพท์
- 📱 **Device Fingerprinting** — อนุญาตเฉพาะโทรศัพท์ที่ลงทะเบียนไว้
- 🤖 **Telegram Bot** แจ้งเตือนเมื่อพนักงานเข้า/ออกงาน พร้อมแจ้งเตือนสาย และใบหน้าแปลกปลอม
- 📊 **Admin Panel** — จัดการพนักงาน, ดูรายงาน, Export CSV
- 🔐 JWT Authentication สำหรับระบบ Admin

---

## การติดตั้ง

### ขั้นที่ 1: ติดตั้ง Dependencies

**Windows — ต้องติดตั้ง Visual Studio Build Tools + CMake ก่อน:**
```bash
pip install cmake
pip install dlib
pip install -r backend/requirements.txt
```

**หรือใช้ Docker (แนะนำ):**
```bash
docker-compose up -d
```

### ขั้นที่ 2: ตั้งค่า Environment Variables

```bash
cp .env.example .env
```

แก้ไขไฟล์ `.env`:
```env
SECRET_KEY=your-random-secret-key-here
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_ADMIN_CHAT_ID=-100xxxxxxxxx
SHIFT_START_TIME=09:00
LATE_THRESHOLD_MINUTES=15
```

### ขั้นที่ 3: รันระบบ

```bash
python run.py
```

เปิด browser:
- **หน้าสแกนหน้า:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/docs

**Login เริ่มต้น:** `admin` / `admin1234` (เปลี่ยนทันทีหลัง login ครั้งแรก)

---

## การตั้งค่า Telegram Bot

1. คุยกับ [@BotFather](https://t.me/botfather) → `/newbot` → รับ Token
2. สร้าง Group สำหรับแจ้งเตือน Admin → เพิ่ม bot เข้า group → เปิด bot เป็น Admin
3. ใช้ [@userinfobot](https://t.me/userinfobot) เพื่อดู Chat ID ของ group (จะขึ้นต้นด้วย `-100`)
4. ใส่ค่าใน `.env`:
   ```
   TELEGRAM_BOT_TOKEN=xxx
   TELEGRAM_ADMIN_CHAT_ID=-100xxxxxxxxx
   ```

---

## วิธีใช้งาน

### 1. เพิ่มพนักงาน
Admin → จัดการพนักงาน → เพิ่มพนักงาน → กรอกข้อมูล

### 2. บันทึกข้อมูลใบหน้า
Admin → จัดการพนักงาน → กดปุ่ม "📸 ใบหน้า" → ถ่ายรูป 3-5 รูป → บันทึก

### 3. ลงทะเบียนอุปกรณ์
เปิดหน้าสแกนหน้าในโทรศัพท์ที่ต้องการ → Admin → จัดการอุปกรณ์ → คัดลอก Fingerprint → ลงทะเบียน

### 4. การเข้างาน
พนักงานเปิดหน้าสแกนหน้าในโทรศัพท์ที่ลงทะเบียน → กดสแกน → ระบบจดจำใบหน้า → บันทึกอัตโนมัติ

---

## โครงสร้างโปรเจค

```
attendance-system/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   │   ├── face_service.py      # Face recognition
│   │   ├── telegram_service.py  # Telegram notifications
│   │   ├── device_service.py    # Device fingerprinting
│   │   └── auth_service.py      # JWT auth
│   ├── middleware/          # Auth & device guards
│   └── face_data/           # Stored face encodings (.npy)
├── frontend/
│   ├── index.html           # หน้าสแกนหน้า (kiosk)
│   ├── admin/               # Admin panel
│   ├── js/                  # JavaScript
│   └── css/                 # Styles
├── run.py                   # Entry point
└── .env.example             # Example config
```

---

## Security Notes

- ต้องใช้ **HTTPS** บน production (กล้องไม่ทำงานบน HTTP บน mobile browser)
- Device Fingerprint ป้องกันการใช้จากอุปกรณ์ที่ไม่ได้รับอนุญาต
- Admin JWT Token หมดอายุใน 30 นาที
- Face data เก็บเป็น numpy encoding ไม่เก็บรูปภาพ

---

## Production Deployment (Nginx + HTTPS)

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```
