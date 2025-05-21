from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from pathlib import Path

# 경로 설정
cert_dir = Path("certs")
cert_dir.mkdir(exist_ok=True)
key_path = cert_dir / "server.key"
crt_path = cert_dir / "server.crt"

# 개인 키 생성
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# 인증서 구성
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "KR"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Seoul"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "nmdose"),
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost")]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

# 파일 저장
with open(key_path, "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open(crt_path, "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f"✅ 인증서 생성 완료: {crt_path}")
print(f"✅ 개인키 생성 완료: {key_path}")
