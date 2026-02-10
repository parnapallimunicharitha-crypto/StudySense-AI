# ======================================================
# 📚 StudySense AI – FINAL VERSION
# ======================================================

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import time
from datetime import date, datetime
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# ======================================================
# DATABASE
# ======================================================

def get_connection():
    return sqlite3.connect("study.db", check_same_thread=False)

conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS study(
datetime TEXT,
subject TEXT,
hours REAL
)
""")
conn.commit()

def add_data(dt, s, h):
    cur.execute("INSERT INTO study VALUES(?,?,?)", (dt, s, h))
    conn.commit()

def view_all():
    cur.execute("SELECT * FROM study")
    return cur.fetchall()

def clear_all_data():
    cur.execute("DELETE FROM study")
    conn.commit()

# ======================================================
# PAGE CONFIG
# ======================================================

st.set_page_config(page_title="StudySense AI", layout="wide")
st.title("📚 StudySense AI Dashboard")

# ======================================================
# LIGHT THEME + BOLD FONT
# ======================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#dbeafe,#e9d5ff);
    color:#111;
    font-weight:600;
}

section[data-testid="stSidebar"] {
    background:#c7d2fe;
}

h1,h2,h3,h4,label,span,p {
    font-weight:700 !important;
}

.stButton>button {
    background:#4f46e5;
    color:white;
    border-radius:12px;
    font-weight:700;
    padding:8px 16px;
}

.stButton>button:hover {
    background:#3730a3;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# SIDEBAR
# ======================================================

mode = st.sidebar.selectbox(
    "📂 Navigate",
    ["Add Study", "Dashboard", "Focus Timer"]
)

# ======================================================
# ➕ ADD STUDY
# ======================================================

if mode == "Add Study":

    st.subheader("➕ Add Study Session")

    subject = st.text_input("Subject")
    hours = st.number_input("Hours", 0.0, 24.0, step=0.5)

    if st.button("Save Study"):

        now = str(datetime.now())
        add_data(now, subject, hours)

        st.balloons()
        st.success("Saved successfully 🎉")

# ======================================================
# 📊 DASHBOARD
# ======================================================

elif mode == "Dashboard":

    data = view_all()

    st.subheader("⚙️ Settings")

    if st.button("🗑️ Clear All Study History"):
        clear_all_data()
        st.success("History cleared ✅")
        st.rerun()

    if len(data) == 0:
        st.info("Add some study first 🌱")

    else:

        # =========================
        # SAFE DATETIME FIX
        # =========================

        df = pd.DataFrame(data, columns=["Datetime", "Subject", "Hours"])

        df["Datetime"] = pd.to_datetime(
            df["Datetime"],
            format="mixed",
            errors="coerce"
        )

        df = df.dropna(subset=["Datetime"])

        df["Date"] = df["Datetime"].dt.date

        today = date.today()
        TARGET = 5

        # ==================================================
        # SUBJECT FILTER
        # ==================================================

        st.subheader("🔍 Subject Filter")

        subjects = ["All"] + list(df["Subject"].unique())

        selected = st.selectbox("Choose Subject", subjects)

        if selected != "All":
            df = df[df["Subject"] == selected]

        # ==================================================
        # DAILY GOAL
        # ==================================================

        st.subheader("🎯 Daily Goal")

        today_total = df[df["Date"] == today]["Hours"].sum()

        st.progress(min(today_total / TARGET, 1))
        st.write(f"### {today_total} / {TARGET} hrs")

        if today_total >= TARGET:
            st.success("Goal Achieved ⭐")
            st.balloons()

        # ==================================================
        # WEEKLY STATS
        # ==================================================

        st.subheader("📅 Weekly Stats")

        last7 = df.tail(7)

        c1, c2 = st.columns(2)
        c1.metric("Last 7 Days", f"{last7['Hours'].sum()} hrs")
        c2.metric("Total Hours", f"{df['Hours'].sum()} hrs")

        # ==================================================
        # SUBJECT CHART (COLORFUL)
        # ==================================================

        st.subheader("📊 Subject Wise Study")

        subject_data = df.groupby("Subject")["Hours"].sum()

        palette = [
            "#4F46E5", "#06B6D4", "#10B981",
            "#F59E0B", "#EF4444", "#8B5CF6",
            "#EC4899"
        ]

        colors = [palette[i % len(palette)] for i in range(len(subject_data))]

        fig, ax = plt.subplots()

        bars = ax.bar(subject_data.index, subject_data.values, color=colors)

        for bar in bars:
            ax.text(
                bar.get_x()+bar.get_width()/2,
                bar.get_height(),
                f"{bar.get_height():.1f}",
                ha="center"
            )

        st.pyplot(fig)

        # ==================================================
        # STREAK (SAFE)
        # ==================================================

        st.subheader("🔥 Study Streak")

        dates = sorted(df["Date"].unique())
        streak = 0

        for d in reversed(dates):
            if (today - d).days == streak:
                streak += 1
            else:
                break

        st.success(f"{streak} days 🔥")

        # ==================================================
        # BADGES
        # ==================================================

        st.subheader("🏆 Badges")

        badges = []

        if today_total >= TARGET:
            badges.append("🎯 Daily Goal Achiever")

        if streak >= 3:
            badges.append("🔥 3 Day Streak")

        if df["Hours"].sum() >= 50:
            badges.append("💪 Study Monster")

        for b in badges:
            st.success(b)

        # ==================================================
        # ML PREDICTION
        # ==================================================

        st.subheader("🤖 Tomorrow Prediction")

        daily_sum = df.groupby("Date")["Hours"].sum().reset_index()

        if len(daily_sum) >= 2:
            X = np.arange(len(daily_sum)).reshape(-1, 1)
            y = daily_sum["Hours"]

            model = LinearRegression()
            model.fit(X, y)

            pred = model.predict([[len(daily_sum)]])[0]

            st.info(f"📈 Predicted: {round(pred,2)} hrs tomorrow")

        # ==================================================
        # MOTIVATION
        # ==================================================

        quotes = [
            "Tiny steps build mountains.",
            "Focus now, freedom later.",
            "Consistency beats intensity.",
            "Your future self is cheering.",
            "One hour today is a victory."
        ]

        st.info("✨ " + np.random.choice(quotes))

        # ==================================================
        # CSV DOWNLOAD
        # ==================================================

        csv = df.to_csv(index=False).encode()

        st.download_button(
            "⬇ Download CSV",
            csv,
            "study_data.csv",
            "text/csv"
        )

        # ==================================================
        # HISTORY
        # ==================================================

        st.subheader("📋 History")
        st.dataframe(df)

# ======================================================
# ⏰ FOCUS TIMER
# ======================================================

elif mode == "Focus Timer":

    st.subheader("🌿 Focus Timer")

    minutes = st.slider("Minutes", 5, 60, 25)

    placeholder = st.empty()

    if st.button("Start Session"):

        total = minutes * 60

        for remaining in range(total, -1, -1):

            mins = remaining // 60
            secs = remaining % 60

            placeholder.markdown(f"# ⏳ {mins:02d}:{secs:02d}")

            if remaining % 300 == 0 and remaining != total:
                st.toast("💧 Drink water!")

            time.sleep(1)

        st.balloons()
        st.success("Session complete ☕")
