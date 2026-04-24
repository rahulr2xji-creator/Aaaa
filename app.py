from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
import binascii
import requests
import json
import uid_generator_pb2
import like_count_pb2
from google.protobuf.message import DecodeError

app = Flask(__name__)

# 🔹 Load token
def load_tokens(server_name):
    try:
        with open("token_ind.json", "r") as f:
            tokens = json.load(f)
        return tokens
    except Exception as e:
        app.logger.error(f"Token load error: {e}")
        return None

# 🔹 Encrypt protobuf
def encrypt_message(plaintext):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext, AES.block_size)
    return binascii.hexlify(cipher.encrypt(padded)).decode()

# 🔹 UID protobuf
def create_protobuf(uid):
    msg = uid_generator_pb2.uid_generator()
    msg.saturn_ = int(uid)
    msg.garena = 1
    return msg.SerializeToString()

def enc(uid):
    return encrypt_message(create_protobuf(uid))

# 🔹 Decode response protobuf
def decode_protobuf(binary):
    try:
        items = like_count_pb2.Info()
        items.ParseFromString(binary)
        return items
    except DecodeError as e:
        app.logger.error(f"Decode error: {e}")
        return None

# 🔹 Request to Free Fire server
def make_request(encrypt, token):
    url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    edata = bytes.fromhex(encrypt)

    headers = {
        'User-Agent': "Dalvik/2.1.0",
        'Authorization': f"Bearer {token}",
        'Content-Type': "application/x-www-form-urlencoded",
        'X-Unity-Version': "2018.4.11f1",
        'ReleaseVersion': "OB53"
    }

    response = requests.post(url, data=edata, headers=headers, verify=False)
    binary = bytes.fromhex(response.content.hex())
    return decode_protobuf(binary)

# 🎯 MAIN PLAYER INFO API
@app.route("/player", methods=["GET"])
def player_info():
    uid = request.args.get("uid")
    if not uid:
        return jsonify({"error": "UID required"}), 400

    tokens = load_tokens("IND")
    if not tokens:
        return jsonify({"error": "Token error"}), 500

    token = tokens[0]["token"]
    encrypted_uid = enc(uid)

    data_proto = make_request(encrypted_uid, token)
    if data_proto is None:
        return jsonify({"error": "Player not found"}), 500

    json_data = json.loads(MessageToJson(data_proto))
    acc = json_data.get("AccountInfo", {})

    result = {
        "PlayerName": acc.get("PlayerNickname", "NA"),
        "PlayerLevel": acc.get("AccountLevel", "NA"),
        "PlayerUID": acc.get("UID", uid)
    }

    return jsonify(result)

@app.route("/")
def home():
    return "Free Fire Player Info API Running"