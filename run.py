"""
สคริปต์สำหรับรัน Attendance System
"""
import uvicorn
import sys
import os
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    # ตรวจสอบว่ามี .env file
    if not os.path.exists("backend/.env") and not os.path.exists(".env"):
        print("WARNING: ไม่พบไฟล์ .env")
        print("   กรุณาสร้างไฟล์ .env จาก .env.example:")
        print("   cp .env.example .env")
        print("   จากนั้นแก้ไขค่าใน .env ให้ถูกต้อง")
        print()

    # ตรวจสอบ SSL cert
    ssl_keyfile = "ssl/key.pem"
    ssl_certfile = "ssl/cert.pem"
    use_https = os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile)

    local_ip = get_local_ip()

    if use_https:
        port = 8443
        scheme = "https"
        print("INFO: กำลังเริ่มต้นระบบสแกนหน้าเข้างาน (HTTPS mode)...")
    else:
        port = 8000
        scheme = "http"
        print("INFO: กำลังเริ่มต้นระบบสแกนหน้าเข้างาน...")
        print("   TIP: รัน 'python generate_cert.py' เพื่อเปิดใช้ HTTPS (จำเป็นสำหรับกล้องบนมือถือ)")

    print(f"   หน้าสแกนหน้า:  {scheme}://localhost:{port}/")
    print(f"   Admin Panel:   {scheme}://localhost:{port}/admin/")
    print(f"   API Docs:      {scheme}://localhost:{port}/docs")
    print(f"   เข้าจากมือถือ: {scheme}://{local_ip}:{port}/")
    print()

    kwargs = dict(
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
    if use_https:
        kwargs["ssl_keyfile"] = ssl_keyfile
        kwargs["ssl_certfile"] = ssl_certfile

    uvicorn.run("backend.main:app", **kwargs)
