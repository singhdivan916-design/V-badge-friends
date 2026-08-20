#!/usr/bin/env python3
import sys
import time
import binascii
import json
import base64
import warnings
from datetime import datetime
from http import HTTPStatus

warnings.filterwarnings("ignore")
import requests
requests.packages.urllib3.disable_warnings()

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from google.protobuf import descriptor_pool, message_factory
import blackboxprotobuf

# ============================================================
# HARDCODE YOUR ACCESS TOKEN HERE
# ============================================================
USER_ACCESS_TOKEN = "0124c9a79d585c25a9175f47ab0c83c52e78451fa56913d4678c5f9ad159e001"   # <-- Replace with your token

# ------------------------------------------------------------
# Constants from original script
# ------------------------------------------------------------
AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

MAJOR_LOGIN_URL = "https://loginbp.ggblueshark.com/MajorLogin"
INSPECT_URL = "https://100067.connect.garena.com/oauth/token/inspect"
ACCOUNT_INFO_URL = "https://ff-jwt-gen-api.lovable.app/api/public/token"

XOR_KEY = b"1e5898ccb8dfdd921f9bdea848768b64a201"

# Protobuf descriptors (copied verbatim)
MY_DESCRIPTOR = b'\n\x08my.proto"\xae\t\n\x08GameData\x12\x11\n\ttimestamp\x18\x03 \x01(\t\x12\x11\n\tgame_name\x18\x04 \x01(\t\x12\x14\n\x0cgame_version\x18\x05 \x01(\x05\x12\x14\n\x0cversion_code\x18\x07 \x01(\t\x12\x0f\n\x07os_info\x18\x08 \x01(\t\x12\x13\n\x0bdevice_type\x18\t \x01(\t\x12\x18\n\x10network_provider\x18\n \x01(\t\x12\x17\n\x0fconnection_type\x18\x0b \x01(\t\x12\x14\n\x0cscreen_width\x18\x0c \x01(\x05\x12\x15\n\rscreen_height\x18\r \x01(\x05\x12\x0b\n\x03dpi\x18\x0e \x01(\t\x12\x10\n\x08cpu_info\x18\x0f \x01(\t\x12\x11\n\ttotal_ram\x18\x10 \x01(\x05\x12\x10\n\x08gpu_name\x18\x11 \x01(\t\x12\x13\n\x0bgpu_version\x18\x12 \x01(\t\x12\x0f\n\x07user_id\x18\x13 \x01(\t\x12\x12\n\nip_address\x18\x14 \x01(\t\x12\x10\n\x08language\x18\x15 \x01(\t\x12\x0f\n\x07open_id\x18\x16 \x01(\t\x12\x15\n\rplatform_type\x18\x17 \x01(\x05\x12\x1a\n\x12device_form_factor\x18\x18 \x01(\t\x12\x14\n\x0cdevice_model\x18\x19 \x01(\t\x12\x14\n\x0caccess_token\x18\x1d \x01(\t\x12\x18\n\x10unknown_field_30\x18\x1e \x01(\x05\x12"\n\x1asecondary_network_provider\x18) \x01(\t\x12!\n\x19secondary_connection_type\x18* \x01(\t\x12\x11\n\tunique_id\x18\x39 \x01(\t\x12\x10\n\x08field_60\x18< \x01(\x05\x12\x10\n\x08field_61\x18= \x01(\x05\x12\x10\n\x08field_62\x18> \x01(\x05\x12\x10\n\x08field_63\x18? \x01(\x05\x12\x10\n\x08field_64\x18@ \x01(\x05\x12\x10\n\x08field_65\x18A \x01(\x05\x12\x10\n\x08field_66\x18B \x01(\x05\x12\x10\n\x08field_67\x18C \x01(\x05\x12\x10\n\x08field_70\x18F \x01(\x05\x12\x10\n\x08field_73\x18I \x01(\x05\x12\x14\n\x0clibrary_path\x18J \x01(\t\x12\x10\n\x08field_76\x18L \x01(\x05\x12\x10\n\x08apk_info\x18M \x01(\t\x12\x10\n\x08field_78\x18N \x01(\x05\x12\x10\n\x08field_79\x18O \x01(\x05\x12\x17\n\x0fos_architecture\x18Q \x01(\t\x12\x14\n\x0cbuild_number\x18S \x01(\t\x12\x10\n\x08field_85\x18U \x01(\x05\x12\x18\n\x10graphics_backend\x18V \x01(\t\x12\x19\n\x11max_texture_units\x18W \x01(\x05\x12\x15\n\rrendering_api\x18X \x01(\x05\x12\x18\n\x10encoded_field_89\x18Y \x01(\t\x12\x10\n\x08field_92\x18\\ \x01(\x05\x12\x13\n\x0bmarketplace\x18] \x01(\t\x12\x16\n\x0eencryption_key\x18^ \x01(\t\x12\x15\n\rtotal_storage\x18_ \x01(\x05\x12\x10\n\x08field_97\x18a \x01(\x05\x12\x10\n\x08field_98\x18b \x01(\x05\x12\x10\n\x08field_99\x18c \x01(\t\x12\x11\n\tfield_100\x18d \x01(\tb\x06proto3'

OUTPUT_DESCRIPTOR = b'\n\x13jwt_generator.proto"\xd2\x02\n\nGarena_420\x12\x12\n\naccount_id\x18\x01 \x01(\x03\x12\x0e\n\x06region\x18\x02 \x01(\t\x12\r\n\x05place\x18\x03 \x01(\t\x12\x10\n\x08location\x18\x04 \x01(\t\x12\x0e\n\x06status\x18\x05 \x01(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\n\n\x02id\x18\t \x01(\x05\x12\x0b\n\x03api\x18\n \x01(\t\x12\x0e\n\x06number\x18\x0c \x01(\x05\x12\x1e\n\tGarena420\x18\x0f \x01(\x0b\x32\x0b.Garena_420\x12\x0c\n\x04area\x18\x10 \x01(\t\x12\x11\n\tmain_area\x18\x12 \x01(\t\x12\x0c\n\x04city\x18\x13 \x01(\t\x12\x0c\n\x04name\x18\x14 \x01(\t\x12\x11\n\ttimestamp\x18\x15 \x01(\x03\x12\x0e\n\x06binary\x18\x16 \x01(\x0c\x12\x13\n\x0bbinary_data\x18\x17 \x01(\x0c\x1a"\n\x12Decrypted_Payloads\x12\x0c\n\x04type\x18\x01 \x01(\x05b\x06proto3'

pool = descriptor_pool.Default()
pool.AddSerializedFile(MY_DESCRIPTOR)
pool.AddSerializedFile(OUTPUT_DESCRIPTOR)

GameData = message_factory.GetMessageClass(pool.FindMessageTypeByName('GameData'))
Garena420 = message_factory.GetMessageClass(pool.FindMessageTypeByName('Garena_420'))

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def encrypt_data(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(data, AES.block_size))

def decrypt_data(data):
    if len(data) % 16 != 0:
        return data
    try:
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        return unpad(cipher.decrypt(data), AES.block_size)
    except:
        return data

def protobuf_decode(data):
    decoded, _ = blackboxprotobuf.decode_message(data)
    return decoded

def inspect_token(access_token):
    url = f"{INSPECT_URL}?token={access_token}"
    headers = {'User-Agent': 'GarenaMSDK/4.0.19P9'}
    resp = requests.get(url, headers=headers, timeout=10, verify=False)
    if resp.status_code != 200:
        raise Exception(f"Inspect failed: {resp.status_code}")
    data = resp.json()
    return data.get('open_id')

def decode_nickname(b64_str):
    try:
        if not b64_str:
            return ""
        b64_str = b64_str.strip()
        b64_str += "=" * ((4 - len(b64_str) % 4) % 4)
        encrypted = base64.b64decode(b64_str)
        decrypted = bytearray()
        for i, byte in enumerate(encrypted):
            key_byte = XOR_KEY[i % len(XOR_KEY)]
            decrypted.append(byte ^ key_byte)
        return decrypted.decode('utf-8', errors='ignore')
    except Exception:
        return b64_str

def fetch_account_info(access_token):
    url = f"{ACCOUNT_INFO_URL}?access_token={access_token}"
    resp = requests.get(url, timeout=10, verify=False)
    if resp.status_code != 200:
        raise Exception(f"Account info API returned {resp.status_code}")
    data = resp.json()
    if not data.get('success', False):
        raise Exception("Account info API indicated failure")
    uid = data.get('account_uid', 'N/A')
    region = data.get('region', 'N/A')
    platform_used = data.get('platform_type_used')
    payload = data.get('jwt_decoded', {}).get('payload', {})
    nick_enc = payload.get('nickname', '')
    nickname = decode_nickname(nick_enc) if nick_enc else 'Unknown'
    return uid, region, nickname, platform_used

# ------------------------------------------------------------
# Caching for serverless (per‑instance)
# ------------------------------------------------------------
_cached_open_id = None
_cached_preferred_platform = None
_cache_time = 0

def get_cached_open_id(access_token):
    global _cached_open_id
    if _cached_open_id is None:
        _cached_open_id = inspect_token(access_token)
    return _cached_open_id

def get_cached_preferred_platform(access_token):
    global _cached_preferred_platform, _cache_time
    if _cached_preferred_platform is None:
        try:
            _, _, _, platform = fetch_account_info(access_token)
            _cached_preferred_platform = platform
        except Exception:
            _cached_preferred_platform = None
    return _cached_preferred_platform

# ------------------------------------------------------------
# Core logic: forward modified request to real MajorLogin
# ------------------------------------------------------------
def generate_majorlogin_response(base_fields, access_token, open_id, preferred_platform=None):
    all_platforms = list(range(1, 10))
    if preferred_platform is not None and preferred_platform in all_platforms:
        platforms = [preferred_platform] + [p for p in all_platforms if p != preferred_platform]
    else:
        platforms = all_platforms

    for plat in platforms:
        try:
            game = GameData()
            # Copy fields from base_fields
            for field_num_str, value in base_fields.items():
                field_num = int(field_num_str)
                field = GameData.DESCRIPTOR.fields_by_number.get(field_num)
                if field is None:
                    continue
                if field.type == field.TYPE_STRING:
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except UnicodeDecodeError:
                            value = value.hex()
                    setattr(game, field.name, str(value))
                elif field.type in (field.TYPE_INT32, field.TYPE_INT64,
                                    field.TYPE_UINT32, field.TYPE_UINT64,
                                    field.TYPE_SINT32, field.TYPE_SINT64):
                    setattr(game, field.name, int(value))
                elif field.type == field.TYPE_BOOL:
                    setattr(game, field.name, bool(value))
                elif field.type == field.TYPE_BYTES:
                    if isinstance(value, str):
                        try:
                            value = binascii.unhexlify(value)
                        except:
                            value = value.encode()
                    setattr(game, field.name, value)
                else:
                    setattr(game, field.name, value)

            game.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            game.open_id = open_id
            game.access_token = access_token
            game.platform_type = plat
            game.field_99 = str(plat)
            game.field_100 = str(plat)

            serialized = game.SerializeToString()
            encrypted = encrypt_data(serialized)
            headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                "Content-Type": "application/octet-stream",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB54"
            }
            resp = requests.post(MAJOR_LOGIN_URL, data=encrypted, headers=headers,
                                 verify=False, timeout=10)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        time.sleep(0.1)
    raise Exception("No valid response after trying all platforms 1-9")

# ------------------------------------------------------------
# WSGI entry point for Vercel (called 'app')
# ------------------------------------------------------------
def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', '')

    # Handle /Ping
    if path == '/Ping' and method == 'GET':
        start_response('200 OK', [('Content-Length', '0'), ('Connection', 'close')])
        return [b'']

    # Handle /MajorLogin
    if path == '/MajorLogin' and method == 'POST':
        try:
            # Read request body
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            body = environ['wsgi.input'].read(content_length) if content_length else b''

            # Decrypt and decode request
            decrypted = decrypt_data(body)
            base_fields = protobuf_decode(decrypted)

            # Obtain open_id (cached)
            open_id = get_cached_open_id(USER_ACCESS_TOKEN)

            # Obtain preferred platform (cached)
            preferred = get_cached_preferred_platform(USER_ACCESS_TOKEN)

            # Generate and forward response
            response_data = generate_majorlogin_response(
                base_fields, USER_ACCESS_TOKEN, open_id, preferred
            )

            start_response('200 OK', [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Length', str(len(response_data))),
                ('Connection', 'close')
            ])
            return [response_data]

        except Exception as e:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [f"Error: {str(e)}".encode()]

    # Any other path
    start_response('404 Not Found', [('Content-Length', '0'), ('Connection', 'close')])
    return [b'']
