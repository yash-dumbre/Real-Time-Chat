from py_vapid import Vapid
import base64
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption
)

v = Vapid()
v.generate_keys()

private = base64.urlsafe_b64encode(
    v.private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.TraditionalOpenSSL,
        NoEncryption()
    )
).decode('utf-8').rstrip('=')

public = base64.urlsafe_b64encode(
    v.public_key.public_bytes(
        Encoding.X962,
        PublicFormat.UncompressedPoint
    )
).decode('utf-8').rstrip('=')

print('VAPID_PRIVATE_KEY =', repr(private))
print('VAPID_PUBLIC_KEY  =', repr(public))