import streamlit as st
import requests
from authlib.integrations.requests_client import OAuth2Session
from firebase_admin import firestore

# --- הגדרות OAuth ---
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]
REDIRECT_URI = "http://localhost:8501"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPE = "openid email profile"

# --- מסך התחברות ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:

    st.title("JobLee – התחברות")
    st.write("התחבר כדי להמשיך")

    # יצירת לינק התחברות
    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope=SCOPE,
        redirect_uri=REDIRECT_URI
    )

    auth_url, state = oauth.create_authorization_url(AUTH_URL)
    st.session_state["oauth_state"] = state

    st.markdown(f"""
        <a href="{auth_url}">
            <button style="
                padding: 12px 24px;
                background-color: #4285F4;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 18px;
                cursor: pointer;
            ">
                🔐 התחבר עם Google
            </button>
        </a>
    """, unsafe_allow_html=True)

    # בדיקת callback
    code = st.query_params.get("code", None)

    if code:
        oauth = OAuth2Session(
            CLIENT_ID,
            CLIENT_SECRET,
            scope=SCOPE,
            redirect_uri=REDIRECT_URI,
            state=st.session_state["oauth_state"]
        )

        token = oauth.fetch_token(
            TOKEN_URL,
            code=code,
            client_secret=CLIENT_SECRET
        )

        user_info = requests.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {token['access_token']}"}
        ).json()

        st.session_state.user = {
            "uid": user_info["sub"],
            "email": user_info["email"],
            "name": user_info.get("name", "")
        }

        st.rerun()

    st.stop()

# --- יצירת מסמך משתמש ב-Firestore ---
db = firestore.client()

def ensure_user_document():
    uid = st.session_state.user["uid"]
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        user_ref.set({
            "uid": uid,
            "email": st.session_state.user["email"],
            "display_name": st.session_state.user.get("name", ""),
            "avatar_style": None,
            "avatar_image": None,
            "xp": 0,
            "level": 1,
            "badges": [],
        })

ensure_user_document()

st.success("מחובר בהצלחה!")
