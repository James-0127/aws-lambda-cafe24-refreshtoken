"""
This function handles the Cafe24 OAuth token refresh process.
"""

import os
from responses import json_response
from cafe24_oauth import request_token_with_refresh, Cafe24APIError
from token_store import upsert_token, TokenStoreError
from db import DBError, now_utc

def lambda_handler(event, context):
    """
    1) (보통은 스케줄러/EventBridge에서 호출)
    2) DB에서 refresh_token 읽고 Cafe24에 재발급 요청
    3) DB upsert 후 결과 반환
    """
    if os.environ.get("AWS_EXECUTION_ENV") is None:
    # 로컬이라고 판단
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=".env.local")
        except Exception as e:
            print("dotenv load skipped or failed:", e)
    
    try:
        token_json = request_token_with_refresh()
    except Cafe24APIError as e:
        return json_response(500, {
            "ok": False,
            "message": "Cafe24 config error",
            "error": str(e),
        })
    except Exception as e:
        return json_response(502, {
            "ok": False,
            "message": "Failed to refresh token from Cafe24",
            "error": str(e),
        })

    try:
        row = upsert_token(token_json)
    except (TokenStoreError, DBError) as e:
        return json_response(500, {
            "ok": False,
            "message": "Failed to store refreshed token",
            "error": str(e),
        })
    except Exception as e:
        return json_response(500, {
            "ok": False,
            "message": "Unexpected DB error",
            "error": str(e),
        })

    return json_response(200, {
        "ok": True,
        "message": "Access token refreshed",
        "data": {
            "token_row_id": row["id"],
            "mall_id": row["mall_id"],
            "issued_at": row["issued_at"],
            "expires_at": row["expires_at"],
            "refreshed_at": now_utc().isoformat(),
        }
    })