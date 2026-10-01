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

# รายชื่อหัวคอลัมน์ใหม่ (รวม 12 คอลัมน์)
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
st.subheader("⏱️ (ส่งภายใน 12.00 น. วันที่ 01.10.2026)")

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
    
    # คำถามหลัก: ได้รับผลกระทบจากน้ำท่วมหรือไม่
    impact_status = st.radio(
        "ได้รับผลกระทบจากน้ำท่วมหรือไม่ *",
        ["ไม่กระทบ", "กระทบ"],
        index=0,
        horizontal=True
    )
    
    # ตัวแปรเก็บค่าเมนูย่อย
    sub_house = False
    sub_surround = False
    sub_accident = False

    # ถ้าตอบ "กระทบ" ให้แสดงเมนูย่อยให้เลือกตอบเพิ่มเติม
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
                        
                        # คำนวณค่า 1 และ 0 ตามการเลือก
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

    # แสดงตารางรายการทั้งหมดแยกตามแผนก
    st.dataframe(df_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🧮 ยอดรวมภาพรวมองค์กร (แยกตามฝ่าย)")
    
    # 1. สรุปรวมยอดแยกตามแต่ละ "ฝ่าย"
    df_by_faction = df_data.groupby("ฝ่าย", as_index=False)[num_cols].sum()
    df_by_faction["แผนก"] = "รวมตามฝ่าย"
    df_by_faction["กลุ่ม"] = "-"
    df_by_faction["ชื่อ-นามสกุล"] = "-"
    df_by_faction = df_by_faction[COLUMNS]

    # 2. สร้างบรรทัดสรุปรวมทั้งหมดองค์กร (Grand Total ทุก Column)
    total_row = {
        "ฝ่าย": "รวมทั้งหมด (Total)", 
        "แผนก": "-", 
        "กลุ่ม": "-", 
        "ชื่อ-นามสกุล": "-"
    }
    for col in num_cols:
        total_row[col] = df_data[col].sum()
    
    df_grand_total = pd.DataFrame([total_row])[COLUMNS]
    
    # 3. รวมตารางสรุปรายฝ่าย และ สรุปรวมทั้งหมด (Grand Total) เข้าด้วยกัน
    df_total_summary = pd.concat([df_by_faction, df_grand_total], ignore_index=True)
    
    # แสดงตารางยอดรวมภาพรวมองค์กร
    st.dataframe(df_total_summary, use_container_width=True, hide_index=True)

else:
    st.info("ℹ️ ยังไม่มีข้อมูลในระบบ หรือยังไม่ได้ตั้งค่า `SHEET_ID` ในไฟล์")
