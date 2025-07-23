import streamlit as st
import pandas as pd
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import threading
import time
import os

# ================================
# GLOBAL VARIABLES
# ================================
log_messages = []
scheduler = BackgroundScheduler()
scheduler.start()
df_data = None
access_token = None
page_id = None

# ================================
# LOG
# ================================
def add_log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_messages.append(f"[{now}] {message}")

# ================================
# UPLOAD VIDEO
# ================================
def post_video_to_page(video_path, caption, comment_text):
    global access_token, page_id
    try:
        url = f"https://graph.facebook.com/{page_id}/videos"
        with open(video_path, 'rb') as f:
            files = {'source': f}
            data = {'description': caption, 'access_token': access_token}
            r = requests.post(url, data=data, files=files)

        if r.status_code == 200:
            video_id = r.json().get('id')
            add_log(f"✅ Video berhasil diupload: {os.path.basename(video_path)} | Video ID: {video_id}")
            if comment_text:
                post_comment_to_video(video_id, comment_text)
        else:
            add_log(f"❌ Gagal upload {os.path.basename(video_path)} | {r.status_code} | {r.text}")
    except Exception as e:
        add_log(f"❌ Error upload {os.path.basename(video_path)} | {e}")

# ================================
# KOMENTAR
# ================================
def post_comment_to_video(video_id, comment_text):
    global access_token
    try:
        url = f"https://graph.facebook.com/{video_id}/comments"
        data = {'message': comment_text, 'access_token': access_token}
        r = requests.post(url, data=data)
        if r.status_code == 200:
            add_log(f"💬 Komentar berhasil ditambahkan ke Video ID: {video_id}")
        else:
            add_log(f"❌ Gagal komentar ke Video ID: {video_id} | {r.status_code} | {r.text}")
    except Exception as e:
        add_log(f"❌ Error komentar: {e}")

# ================================
# CEK JADWAL
# ================================
def cek_jadwal():
    global df_data
    if df_data is None:
        return
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    for _, row in df_data.iterrows():
        jadwal_str = pd.to_datetime(row['jadwal_publish']).strftime("%Y-%m-%d %H:%M")
        if jadwal_str == now_str:
            post_video_to_page(row['file_path'], row['caption'], row.get('komentar',''))

# ================================
# BACKGROUND SCHEDULER
# ================================
def run_scheduler():
    while True:
        cek_jadwal()
        time.sleep(60)

# ================================
# STREAMLIT UI
# ================================
st.title("📌 Scheduler Upload Video + Komentar ke Facebook Page")

# Input token & page ID
access_token = st.text_input("🔑 Masukkan Page Access Token", type="password")
page_id = st.text_input("🆔 Masukkan Page ID")

# Upload file excel
uploaded_file = st.file_uploader("📥 Upload File XLSX")
if uploaded_file is not None:
    try:
        df_data = pd.read_excel(uploaded_file)
        st.success("✅ Data berhasil diimport!")
        st.dataframe(df_data)
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")

# Manual eksekusi
if st.button("🚀 Eksekusi Manual Sekarang"):
    if df_data is not None:
        for _, row in df_data.iterrows():
            post_video_to_page(row['file_path'], row['caption'], row.get('komentar',''))
        st.success("✅ Semua posting dieksekusi sekarang.")
    else:
        st.warning("⚠️ Data belum diimport.")

# Scheduler background
if 'scheduler_started' not in st.session_state:
    st.session_state.scheduler_started = True
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    add_log("Scheduler dimulai...")

# Log Monitor
st.subheader("📋 Log Monitor")
for m in reversed(log_messages[-50:]):
    st.text(m)
