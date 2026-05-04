import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
TG_INFO_API = "https://tginfo-production-1326.up.railway.app/"
# আপনার দেওয়া নতুন API (TG2Phone)
PHONE_LOOKUP_API = "https://m.apisuite.in/?api=TG2Phone&api_key=dacde71d942fd69e434672ea73ae8cfa&id="

def clean_target(target):
    if not target:
        return target
    target = str(target).strip()
    if target.startswith('@'):
        return target[1:]
    return target

def is_numeric(value):
    return str(value).isdigit()

@app.route('/lookup', methods=['GET'])
def premium_lookup():
    raw_target = request.args.get('user')
    
    if not raw_target:
        return jsonify({
            "success": False,
            "status": "Bad Request",
            "message": "Username or Chat ID is required."
        }), 400

    target = clean_target(raw_target)

    try:
        tg_data = {}
        extracted_id = None

        # -------------------------
        # ✅ STEP 1: FETCH BASIC TG INFO (USERNAME OR ID)
        # -------------------------
        # ইউজারনেম হোক বা আইডি, আগে বেসিক ইনফো এপিআই কল করছি আইডি পাওয়ার জন্য
        try:
            tg_res = requests.get(f"{TG_INFO_API}?user={target}", timeout=15)
            tg_data = tg_res.json()
            
            if tg_data.get("success"):
                extracted_id = tg_data.get("id")
            elif is_numeric(target):
                extracted_id = target
        except:
            if is_numeric(target):
                extracted_id = target

        if not extracted_id:
            return jsonify({
                "success": False,
                "status": "Not Found",
                "message": "Could not resolve Telegram entity."
            }), 404

        # -------------------------
        # ✅ STEP 2: FETCH PHONE INFO (NEW API)
        # -------------------------
        phone_info = {}
        try:
            phone_res = requests.get(f"{PHONE_LOOKUP_API}{extracted_id}", timeout=15)
            if phone_res.status_code == 200:
                phone_info = phone_res.json()
        except:
            phone_info = {}

        # -------------------------
        # ✅ FINAL PREMIUM RESPONSE (MERGED DATA)
        # -------------------------
        premium_response = {
            "success": True,
            "developer_credit": "SB-SAKIB | @sakib01994",
            "execution_status": "Success",

            "data": {
                "profile_summary": {
                    "uid": str(extracted_id),
                    "username": f"@{tg_data.get('username')}" if tg_data.get("username") else (
                        f"@{target}" if not is_numeric(target) else "N/A"
                    ),
                    "full_name": f"{tg_data.get('first_name', '')} {tg_data.get('last_name', '')}".strip() or "N/A",
                    "bio": tg_data.get("bio", "Not Available"),
                    "profile_picture": tg_data.get("public_view", {}).get("web_image", "No Image"),
                    "is_premium_account": tg_data.get("premium_user", False),
                },

                "account_status": {
                    "is_bot": tg_data.get("is_bot", False),
                    "is_active": True,
                    "is_scam": tg_data.get("is_scam", False),
                    "is_verified": tg_data.get("is_verified", False),
                },

                "contact_intelligence": {
                    "phone_number": phone_info.get("number") if phone_info.get("success") else tg_data.get("phone", "Private"),
                    "country": phone_info.get("country", "Unknown"),
                    "country_code": phone_info.get("country_code", "N/A"),
                },

                "security_trust_score": {
                    "is_fake": tg_data.get("is_fake", False),
                    "data_leak_status": tg_data.get("leaked_info", "Safe/Unknown"),
                    "status_msg": phone_info.get("msg", "Fetched")
                }
            },

            "system_links": {
                "direct_telegram": f"https://t.me/{tg_data.get('username')}" if tg_data.get('username') else None,
                "support_dev": "https://t.me/sakib01994"
            }
        }

        return jsonify(premium_response), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "status": "Internal Error",
            "message": "An unexpected error occurred.",
            "debug": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)
