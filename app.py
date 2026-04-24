import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import like_count_pb2

urllib3.disable_warnings()

# 🔐 Guest login (token generator)
GUEST_UID = "4086343648"
GUEST_PASSWORD = "MAZID_LWU3Q1XY8K"

BASE_URL = "https://client.ind.freefiremobile.com"

# AES Keys
KEY = b'Yg&tc%DEuh6%Zc^8'
IV  = b'6oyZDr22E3ychjM%'


# ---------------- AES ----------------
def encrypt(data):
    return AES.new(KEY, AES.MODE_CBC, IV).encrypt(pad(data, 16))

def decrypt(data):
    return unpad(AES.new(KEY, AES.MODE_CBC, IV).decrypt(data), 16)


# -------- UID → protobuf --------
def uid_to_protobuf(uid):
    def to_varint(n):
        out = bytearray()
        while n >= 0x80:
            out.append((n & 0x7f) | 0x80)
            n >>= 7
        out.append(n)
        return bytes(out)

    return encrypt(b"\x08" + to_varint(int(uid)))


# -------- JWT TOKEN --------
def get_token():
    url = f"https://papajwt.vercel.app/kirito??uid={GUEST_UID}&password={GUEST_PASSWORD}"
    r = requests.get(url, timeout=10)
    return r.json()["token"]


# -------- DECODE PLAYER INFO --------
def decode_player(binary):
    msg = like_count_pb2.Info()
    msg.ParseFromString(binary)

    acc = msg.AccountInfo
    return {
        "name": acc.PlayerNickname,
        "level": acc.AccountLevel,
        "uid": acc.UID
    }


# -------- MAIN FUNCTION --------
def get_player_info(uid):
    token = get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Android 11)",
        "ReleaseVersion": "OB53"
    }

    payload = uid_to_protobuf(uid)

    r = requests.post(
        f"{BASE_URL}/GetPlayerPersonalShow",
        headers=headers,
        data=payload,
        verify=False,
        timeout=10
    )

    decrypted = decrypt(r.content)
    return decode_player(decrypted)


# -------- RUN --------
if __name__ == "__main__":
    uid = input("Enter Player UID: ")
    info = get_player_info(uid)

    print("\n🔥 PLAYER INFO\n")
    print("Player Name  :", info["name"])
    print("Player Level :", info["level"])
    print("Player UID   :", info["uid"])