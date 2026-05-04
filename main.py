import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- APIs ---
TG_INFO_API = "https://tginfo-production-1326.up.railway.app/"
# আপনার দেওয়া নতুন এপিআই (যেটি থেকে আপনি JSON রেসপন্স পাঠিয়েছেন)
NEW_DATA_API = "https://num-tg-info-api.vercel.app/info?id="

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

        # ---------------------------------------------------------
        # ✅ STEP 1: RESOLVE ID (ইউজারনেম বা আইডি থেকে আইডি বের করা)
        # ---------------------------------------------------------
        if not is_numeric(target):
            # ইউজারনেম হলে আইডি খোঁজা
            try:
                tg_res = requests.get(f"{TG_INFO_API}?user={target}", timeout=15)
                tg_data = tg_res.json()
                if tg_data.get("success"):
                    extracted_id = tg_data.get("id")
            except:
                pass
        else:
            extracted_id = target
            # আইডির ক্ষেত্রে এক্সট্রা ডিটেইলস (বায়ো, ছবি) এর জন্য মেইন এপিআই কল
            try:
                tg_res = requests.get(f"{TG_INFO_API}?user={target}", timeout=10)
                tg_data = tg_res.json()
            except:
                tg_data = {}

        if not extracted_id:
            return jsonify({
                "success": False,
                "status": "Not Found",
                "message": "User information could not be retrieved."
            }), 404

        # ---------------------------------------------------------
        # ✅ STEP 2: FETCH FROM NEW API (আপনার দেওয়া নতুন ডাটা সোর্স)
        # ---------------------------------------------------------
        new_res = requests.get(f"{NEW_DATA_API}{extracted_id}", timeout=15)
        api_result = new_res.json() if new_res.status_code == 200 else {}
        
        # এপিআই রেসপন্স থেকে ডেটা আলাদা করা
        remote_data = api_result.get("data", {})
        basic = remote_data.get("BASIC_INFO", {})
        activity = remote_data.get("ACTIVITY_INFO", {})
        number = remote_data.get("NUMBER_INFO", {})
        status = remote_data.get("STATUS_INFO", {})

        # ---------------------------------------------------------
        # ✅ FINAL PREMIUM RESPONSE (১০০% মার্জড ডাটা)
        # ---------------------------------------------------------
        premium_response = {
            "success": True,
            "developer_credit": "SB-SAKIB | @sakib01994",
            "execution_status": "Success",

            "data": {
                "profile_summary": {
                    "uid": str(basic.get("ID") or extracted_id),
                    "username": f"@{tg_data.get('username')}" if tg_data.get("username") else (
                        f"@{target}" if not is_numeric(target) else "N/A"
                    ),
                    "full_name": (
                        basic.get("FIRST_NAME", "").strip() 
                        or f"{tg_data.get('first_name', '')} {tg_data.get('last_name', '')}".strip() 
                        or "N/A"
                    ),
                    "bio": tg_data.get("bio", "Not Available"),
                    "profile_picture": tg_data.get("public_view", {}).get("web_image", "No Image"),
                    "is_premium_account": tg_data.get("premium_user", False),
                    "name_history_count": basic.get("NAMES_COUNT", 0),
                    "username_history_count": basic.get("USERNAMES_COUNT", 0)
                },

                "account_status": {
                    "is_bot": status.get("IS_BOT", tg_data.get("is_bot", False)),
                    "is_active": status.get("IS_ACTIVE", True),
                    "is_scam": tg_data.get("is_scam", False),
                    "is_verified": tg_data.get("is_verified", False),
                },

                "activity_intelligence": {
                    "first_seen": activity.get("FIRST_MSG_DATE"),
                    "last_seen": activity.get("LAST_MSG_DATE"),
                    "total_messages": activity.get("TOTAL_MSG_COUNT"),
                    "group_messages": activity.get("MSG_IN_GROUPS_COUNT"),
                    "admin_in_groups": activity.get("ADM_IN_GROUPS"),
                    "total_groups": activity.get("TOTAL_GROUPS")
                },

                "contact_intelligence": {
                    "phone_number": number.get("NUMBER", tg_data.get("phone", "Private")),
                    "country": number.get("COUNTRY", "Unknown"),
                    "country_code": number.get("COUNTRY_CODE", "N/A"),
                },

                "security_trust_score": {
                    "is_fake": tg_data.get("is_fake", False),
                    "data_leak_status": tg_data.get("leaked_info", "Unknown"),
                    "api_source_credit": api_result.get("credit", "@ab_devs")
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
            "message": "Something went wrong.",
            "debug": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=False)
