import time
import pyotp
import qrcode


class MfaService:
    SECRET_KEY = "KNSWG5LSMVBWQYLUKJXW63I="

    def generate_qrcode(self, name, issuer_name):
        totp_auth = pyotp.totp.TOTP(self.SECRET_KEY).provisioning_uri(name=name, issuer_name=issuer_name);
        qrcode.make(totp_auth).save("qr_auth.png")

    def verify(self, code):
        totp = pyotp.TOTP(self.SECRET_KEY)
        return  totp.verify(code)

mfa_service = MfaService()
mfa_service.generate_qrcode('Tek-Up', 'Secure Chat Room')

