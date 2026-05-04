Import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# APIs
TG_INFO_API = "https://tginfo-production-1326.up.railway.app/"
NEW_API = "https://num-tg-info-api.vercel.app/info?id="

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
        # ✅ CASE 1: USERNAME
        # -------------------------
        if not is_numeric(target):
            tg_res = requests.get(f"{TG_INFO_API}?user={target}", timeout=15)
            tg_data = tg_res.json()

            if not tg_data.get("success"):
                return jsonify({
                    "success": False,
                    "status": "Not Found",
                    "message": "No data found for this entity.",
                    "api_response": tg_data
                }), 404

            extracted_id = tg_data.get("id")

        # -------------------------
        # ✅ CASE 2: CHAT ID
        # -------------------------
        else:
            extracted_id = target

            # optional TG fetch (extra info পাওয়ার জন্য)
            try:
                tg_res = requests.get(f"{TG_INFO_API}?user={target}", timeout=10)
                tg_data = tg_res.json()
            except:
                tg_data = {}

        # -------------------------
        # ✅ NEW API CALL
        # -------------------------
        new_res = requests.get(f"{NEW_API}{extracted_id}", timeout=15)
        new_data = new_res.json() if new_res.status_code == 200 else {}

        result = new_data.get("RESULT", {})
        basic = result.get("BASIC_INFO", {})
        status = result.get("STATUS_INFO", {})
        activity = result.get("ACTIVITY_INFO", {})
        number = result.get("NUMBER_INFO", {})

        # -------------------------
        # ✅ FINAL PREMIUM RESPONSE
        # -------------------------
        premium_response = {
            "success": True,
            "developer_credit": "SB-SAKIB | @sakib01994",
            "execution_status": "Success",

            "data": {
                "profile_summary": {
                    "uid": basic.get("ID", extracted_id),

                    "username": f"@{tg_data.get('username')}" if tg_data.get("username") else (
                        f"@{target}" if not is_numeric(target) else "N/A"
                    ),

                    "full_name": (
                        f"{basic.get('FIRST_NAME', '')} {basic.get('LAST_NAME') or ''}".strip()
                        or f"{tg_data.get('first_name', '')} {tg_data.get('last_name', '')}".strip()
                        or "N/A"
                    ),

                    "bio": tg_data.get("bio", "Not Available"),
                    "profile_picture": tg_data.get("public_view", {}).get("web_image", "No Image"),

                    "is_premium_account": tg_data.get("premium_user", False),

                    "total_usernames": basic.get("USERNAMES_COUNT"),
                    "name_history": basic.get("NAMES_COUNT"),
                },

                "account_status": {
                    "is_bot": status.get("IS_BOT", tg_data.get("is_bot", False)),
                    "is_active": status.get("IS_ACTIVE", True),
                },

                "activity_intelligence": {
                    "first_seen": activity.get("FIRST_MSG_DATE"),
                    "last_seen": activity.get("LAST_MSG_DATE"),
                    "total_messages": activity.get("TOTAL_MSG_COUNT"),
                    "group_messages": activity.get("MSG_IN_GROUPS_COUNT"),
                    "admin_in_groups": activity.get("ADM_IN_GROUPS"),
                    "total_groups": activity.get("TOTAL_GROUPS"),
                },

                "contact_intelligence": {
                    "phone_number": number.get("NUMBER", tg_data.get("phone", "Private")),
                    "country": number.get("COUNTRY"),
                    "country_code": number.get("COUNTRY_CODE"),
                },

                "security_trust_score": {
                    "is_bot": tg_data.get("is_bot", False),
                    "is_scam": tg_data.get("is_scam", False),
                    "is_fake": tg_data.get("is_fake", False),
                    "is_verified": tg_data.get("is_verified", False),
                    "data_leak_status": tg_data.get("leaked_info", "Unknown")
                }
            },

            "system_links": {
                "direct_telegram": tg_data.get("public_view", {}).get("telegram_link"),
                "support_dev": "https://t.me/sakib01994"
            }
        }

        return jsonify(premium_response), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "status": "Internal Error",
            "message": "Unexpected error occurred.",
            "debug": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=False)

 