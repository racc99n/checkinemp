"""
สร้าง self-signed SSL certificate สำหรับ HTTPS
"""
import datetime
import ipaddress
import socket
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def get_local_ip():
    """หา IP ทุก interface แล้วเลือก 192.168.x.x ก่อน"""
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ":" not in ip:  # IPv4 only
                ips.append(ip)
    except Exception:
        pass
    # เลือก 192.168.x.x ก่อน
    for ip in ips:
        if ip.startswith("192.168."):
            return ip
    # fallback
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def generate_cert():
    local_ip = get_local_ip()
    hostname = socket.gethostname()
    print(f"Generating cert for IP: {local_ip}, hostname: {hostname}")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, local_ip),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Attendance System"),
    ])

    san_ips = [ipaddress.IPv4Address("127.0.0.1")]
    if local_ip != "127.0.0.1":
        san_ips.append(ipaddress.IPv4Address(local_ip))

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName(hostname),
                *[x509.IPAddress(ip) for ip in san_ips],
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    os.makedirs("ssl", exist_ok=True)

    with open("ssl/key.pem", "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open("ssl/cert.pem", "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print("Created: ssl/cert.pem and ssl/key.pem")
    print(f"\nAccess from phone: https://{local_ip}:8443/")
    print(f"Local PC:          https://localhost:8443/")
    print("(ต้องกด 'Advanced' > 'Proceed' เพื่อข้าม security warning ครั้งแรก)")

if __name__ == "__main__":
    generate_cert()
