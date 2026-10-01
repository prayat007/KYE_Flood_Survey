import os
import ssl
import json
import urllib3
import requests
import gspread
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# ✅ SSL & Connection Settings
# ---------------------------------------------------------
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------
# ✅ Config & Sheet Setting
# ---------------------------------------------------------
SHEET_ID = "1-9SAunNI81-u0I1zqULEa6JbFlWQjmJQ-HoAN4HkLUc"

# รายชื่อหัวคอลัมน์ทั้งหมด (รวม 12 คอลัมน์)
COLUMNS = [
    "ฝ่าย",
    "แผนก",
    "กลุ่ม",
    "ชื่อ-นามสกุล",
    "ได้รับผลกระทบจากน้ำท่วม: กระทบ",
    "ได้รับผลกระทบจากน้ำท่วม: ไม่กระทบ",
    "ผลกระทบย่อย: บ้านน้ำท่วม",
    "ผลกระทบย่อย: น้ำท่วมโดยรอบ",
    "ผลกระทบย่อย: ได้รับอุบัติเหตุ",
    "มาทำงานได้",
    "มาทำงานไม่ได้: น้ำท่วมบ้านมาไม่ได้",
    "มาทำงานไม่ได้: น้ำท่วมถนน พื้นที่โดยรอบมาไม่ได้"
]

# ระบุคอลัมน์ที่เป็นข้อความเพื่อไม่ให้นำมารวมยอดตัวเลข
TEXT_COLUMNS = ["ฝ่าย", "แผนก", "กลุ่ม", "ชื่อ-นามสกุล"]

# ---------------------------------------------------------
# 📊 Google Sheets Connection
# ---------------------------------------------------------
@st.cache_resource(ttl=5)
def get_gspread_client():
    try:
        credentials = dict(st.secrets["gcp_service_account"])
        if "private_key" in credentials:
            credentials["private_key"] = credentials["private_key"].replace("\\n", "\n")
        return gspread.service_account_from_dict(credentials)
    except Exception as e:
        st.error(f"❌ โหลดสิทธิ์ GCP ล้มเหลว: {repr(e)}")
        return None

def fetch_data():
    gc = get_gspread_client()
    if not gc or SHEET_ID == "YOUR_GOOGLE_SHEET_ID_HERE":
        return pd.DataFrame(columns=COLUMNS)
    
    try:
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.get_worksheet(0)
        values = worksheet.get_all_values()
        
        # ปรับแก้หัวตารางให้ตรงกันอัตโนมัติ (A1 ถึง L1 รวม 12 คอลัมน์)
        if len(values) == 0 or values[0] != COLUMNS:
            worksheet.update(range_name='A1:L1', values=[COLUMNS])
            values = worksheet.get_all_values()

        if len(values) > 1:
            df = pd.DataFrame(values[1:], columns=values[0])
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS]
        return pd.DataFrame(columns=COLUMNS)
    except Exception as err:
        st.error(f"⚠️ ดึงข้อมูลล้มเหลว: {repr(err)}")
        return pd.DataFrame(columns=COLUMNS)

# ---------------------------------------------------------
# 🖥️ Streamlit UI
# ---------------------------------------------------------
st.set_page_config(page_title="แบบสำรวจผลกระทบน้ำท่วม", page_icon="🌊", layout="wide")

st.title("🌊 แบบสำรวจผลกระทบน้ำท่วม")
st.subheader("⏱️ (ส่งภายใน 12.00 น. วันที่ 30.09.2026)")

st.divider()

# ---------------------------------------------------------
# 💡 POP-UP MODAL บันทึกข้อมูล
# ---------------------------------------------------------
@st.dialog("➕ บันทึก / แก้ไขข้อมูลผลกระทบน้ำท่วม")
def show_survey_modal():
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        faction = st.selectbox("ฝ่าย *", ["QA"])
        group_name = st.selectbox("กลุ่ม", ["G.71", "G.72", "-"])
    with col_d2:
        dept = st.selectbox("แผนก *", ["QEC", "CSV"])
        full_name = st.text_input("ชื่อ-นามสกุล *", placeholder="เช่น นายสมชาย ใจดี")

    st.markdown("---")
    st.markdown("### 1️⃣ สรุปการได้รับผลกระทบ")
    
    impact_status = st.radio(
        "ได้รับผลกระทบจากน้ำท่วมหรือไม่ *",
        ["ไม่กระทบ", "กระทบ"],
        index=0,
        horizontal=True
    )
    
    sub_house = False
    sub_surround = False
    sub_accident = False

    if impact_status == "กระทบ":
        st.info("💡 กรุณาเลือกรายละเอียดผลกระทบที่ได้รับ (เลือกตอบได้มากกว่า 1 ข้อ):")
        sub_house = st.checkbox("🏠 บ้านน้ำท่วม")
        sub_surround = st.checkbox("🌊 น้ำท่วมโดยรอบ")
        sub_accident = st.checkbox("🚑 ได้รับอุบัติเหตุ")

    st.markdown("---")
    st.markdown("### 2️⃣ สถานะการมาทำงาน")
    can_work_option = st.radio("สถานะการมาทำงาน", ["มาทำงานได้", "มาทำงานไม่ได้"], index=0, horizontal=True)
    
    cant_work_house = False
    cant_work_road = False
    if can_work_option == "มาทำงานไม่ได้":
        st.info("💡 กรุณาระบุสาเหตุที่มาทำงานไม่ได้:")
        cant_work_house = st.checkbox("น้ำท่วมบ้านมาไม่ได้")
        cant_work_road = st.checkbox("น้ำท่วมถนน/พื้นที่โดยรอบมาไม่ได้")

    col_save, col_close = st.columns([1, 1])
    with col_save:
        if st.button("💾 บันทึกข้อมูลลง Google Sheets", type="primary", use_container_width=True):
            if not full_name.strip():
                st.warning("⚠️ กรุณากรอก 'ชื่อ-นามสกุล'")
            else:
                try:
                    gc = get_gspread_client()
                    if gc:
                        sh = gc.open_by_key(SHEET_ID)
                        worksheet = sh.get_worksheet(0)
                        
                        affected_val = "1" if impact_status == "กระทบ" else "0"
                        not_affected_val = "1" if impact_status == "ไม่กระทบ" else "0"
                        
                        sub_house_val = "1" if sub_house else "0"
                        sub_surround_val = "1" if sub_surround else "0"
                        sub_accident_val = "1" if sub_accident else "0"
                        
                        can_work_val = "1" if can_work_option == "มาทำงานได้" else "0"
                        cant_house_val = "1" if cant_work_house else "0"
                        cant_road_val = "1" if cant_work_road else "0"

                        new_row = [
                            faction,
                            dept,
                            group_name,
                            full_name.strip(),
                            affected_val,
                            not_affected_val,
                            sub_house_val,
                            sub_surround_val,
                            sub_accident_val,
                            can_work_val,
                            cant_house_val,
                            cant_road_val
                        ]
                        
                        worksheet.append_row(new_row)
                        st.toast(f"✅ บันทึกข้อมูลเรียบร้อยแล้ว!", icon="🎉")
                        st.cache_resource.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาดในการบันทึก: {repr(e)}")

    with col_close:
        if st.button("❌ ยกเลิก", use_container_width=True):
            st.rerun()

# ---------------------------------------------------------
# 🔘 ปุ่มควบคุม
# ---------------------------------------------------------
col_b1, col_b2 = st.columns([2, 1])
with col_b1:
    if st.button("➕ กรอกข้อมูลแบบสำรวจใหม่", type="primary"):
        show_survey_modal()
with col_b2:
    if st.button("🔄 รีเฟรชข้อมูล"):
        st.cache_resource.clear()
        st.rerun()

# ---------------------------------------------------------
# 📊 แสดงผลตารางและสรุปยอด
# ---------------------------------------------------------
st.markdown("### 📋 สรุปผลการสำรวจแยกตามแผนก")
df_data = fetch_data()

if not df_data.empty:
    num_cols = [c for c in COLUMNS if c not in TEXT_COLUMNS]
    
    # แปลงคอลัมน์ตัวเลขให้เป็น int
    for col in num_cols:
        df_data[col] = pd.to_numeric(df_data[col], errors='coerce').fillna(0).astype(int)

    # แสดงตารางข้อมูลรายละเอียด
    st.dataframe(df_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 📊 สรุปภาพรวมองค์กร (Executive Summary)")

    total_employees = len(df_data)

    if total_employees > 0:
        # คำนวณสถานะการมาทำงานแบบรายคน (ไม่ให้นับซ้ำ)
        df_data["มาทำงานไม่ได้_count"] = (
            (df_data["มาทำงานไม่ได้: น้ำท่วมบ้านมาไม่ได้"] == 1) | 
            (df_data["มาทำงานไม่ได้: น้ำท่วมถนน พื้นที่โดยรอบมาไม่ได้"] == 1)
        ).astype(int)
        
        df_data["มาทำงานได้_count"] = (df_data["มาทำงานไม่ได้_count"] == 0).astype(int)

        # สรุปผลกระทบ
        affected_mask = (
            (df_data["ได้รับผลกระทบจากน้ำท่วม: กระทบ"] == 1) | 
            (df_data["ผลกระทบย่อย: บ้านน้ำท่วม"] == 1) | 
            (df_data["ผลกระทบย่อย: น้ำท่วมโดยรอบ"] == 1) | 
            (df_data["ผลกระทบย่อย: ได้รับอุบัติเหตุ"] == 1)
        )
        affected_count = int(affected_mask.sum())
        not_affected_count = total_employees - affected_count

        affected_pct = (affected_count / total_employees) * 100
        not_affected_pct = (not_affected_count / total_employees) * 100

        cant_work_count = int(df_data["มาทำงานไม่ได้_count"].sum())
        can_work_count = total_employees - cant_work_count

        can_work_pct = (can_work_count / total_employees) * 100
        cant_work_pct = (cant_work_count / total_employees) * 100

        # แสดงผลสรุปด้วย Metric Cards
        col_m1, col_m2 = st.columns(2)

        with col_m1:
            st.subheader("🌊 ด้านการได้รับผลกระทบ")
            st.metric("ได้รับผลกระทบ", f"{affected_count} คน", f"{affected_pct:.1f}% ของทั้งหมด")
            st.metric("ไม่ได้รับผลกระทบ", f"{not_affected_count} คน", f"{not_affected_pct:.1f}% ของทั้งหมด")

        with col_m2:
            st.subheader("🚗 ด้านสถานะการมาทำงาน")
            st.metric("มาทำงานได้", f"{can_work_count} คน", f"{can_work_pct:.1f}% ของทั้งหมด")
            st.metric("มาทำงานไม่ได้", f"{cant_work_count} คน", f"{cant_work_pct:.1f}% ของทั้งหมด")

        st.caption(f"👥 **รวมพนักงานที่ตอบแบบสำรวจทั้งหมด:** {total_employees} คน (100.0%)")

        st.markdown("---")
        
        # 📋 ตารางสรุปภาพรวมแยกตาม "ฝ่าย" (เฉพาะการมาทำงานและเปอร์เซ็นต์)
        st.markdown("### 🧮 ยอดรวมการมาทำงานแยกตามฝ่าย")

        df_faction = df_data.groupby("ฝ่าย").agg(
            can_work=("มาทำงานได้_count", "sum"),
            cant_work=("มาทำงานไม่ได้_count", "sum"),
            total_emp=("ชื่อ-นามสกุล", "count")
        ).reset_index()

        df_faction["มาทำงานได้ (คน)"] = df_faction["can_work"].astype(str) + " คน"
        df_faction["มาทำงานได้ (%)"] = (df_faction["can_work"] / df_faction["total_emp"] * 100).map("{:.1f}%".format)
        
        df_faction["มาทำงานไม่ได้ (คน)"] = df_faction["cant_work"].astype(str) + " คน"
        df_faction["มาทำงานไม่ได้ (%)"] = (df_faction["cant_work"] / df_faction["total_emp"] * 100).map("{:.1f}%".format)
        
        df_faction["รวมทั้งหมด (คน)"] = df_faction["total_emp"].astype(str) + " คน"
        df_faction["คิดเป็น % ของผลรวมทั้งหมด"] = (df_faction["total_emp"] / total_employees * 100).map("{:.1f}%".format)

        display_faction_cols = [
            "ฝ่าย",
            "มาทำงานได้ (คน)",
            "มาทำงานได้ (%)",
            "มาทำงานไม่ได้ (คน)",
            "มาทำงานไม่ได้ (%)",
            "รวมทั้งหมด (คน)",
            "คิดเป็น % ของผลรวมทั้งหมด"
        ]
        
        df_faction_display = df_faction[display_faction_cols]

        total_faction_row = pd.DataFrame([{
            "ฝ่าย": "รวมทั้งหมด (Total)",
            "มาทำงานได้ (คน)": f"{can_work_count} คน",
            "มาทำงานได้ (%)": f"{can_work_pct:.1f}%",
            "มาทำงานไม่ได้ (คน)": f"{cant_work_count} คน",
            "มาทำงานไม่ได้ (%)": f"{cant_work_pct:.1f}%",
            "รวมทั้งหมด (คน)": f"{total_employees} คน",
            "คิดเป็น % ของผลรวมทั้งหมด": "100.0%"
        }])

        df_faction_final = pd.concat([df_faction_display, total_faction_row], ignore_index=True)

        st.dataframe(df_faction_final, use_container_width=True, hide_index=True)

else:
    st.info("ℹ️ ยังไม่มีข้อมูลในระบบ หรือยังไม่ได้ตั้งค่า `SHEET_ID` ในไฟล์")
