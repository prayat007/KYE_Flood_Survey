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

# รายชื่อหัวคอลัมน์ทั้ง 11 คอลัมน์
COLUMNS = [
    "ฝ่าย",
    "แผนก",
    "กลุ่ม",
    "ชื่อ-นามสกุล",
    "ไม่ได้รับผลกระทบ",
    "ได้รับผลกระทบ: บาดเจ็บ",
    "ได้รับผลกระทบ: บ้าน",
    "ได้รับผลกระทบ: ทรัพย์สิน",
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
        
        # ปรับแก้หัวตารางให้ตรงกันอัตโนมัติ (A1 ถึง K1 รวม 11 คอลัมน์)
        if len(values) == 0 or values[0] != COLUMNS:
            worksheet.update(range_name='A1:K1', values=[COLUMNS])
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
st.subheader("⏱️ (ส่งภายใน 12.00 น. วันที่ 02.10.2026)")

st.divider()

# ---------------------------------------------------------
# 💡 POP-UP MODAL บันทึกข้อมูล (ปรับเป็น ใช่ / ไม่ใช่)
# ---------------------------------------------------------
@st.dialog("➕ บันทึก / แก้ไขข้อมูลผลกระทบน้ำท่วม")
def show_survey_modal():
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        faction = st.text_input("ฝ่าย *", placeholder="เช่น ฝ่ายผลิต")
        group_name = st.text_input("กลุ่ม", placeholder="เช่น กลุ่มงาน A")
    with col_d2:
        dept = st.text_input("แผนก *", placeholder="เช่น HR, IT")
        full_name = st.text_input("ชื่อ-นามสกุล", placeholder="เช่น นายสมชาย ใจดี")

    options = ["ไม่ใช่", "ใช่"]

    st.markdown("---")
    st.markdown("### 1️⃣ สรุปการได้รับผลกระทบ")
    no_impact = st.radio("ไม่ได้รับผลกระทบ", options, index=0, horizontal=True)
    
    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        injured = st.radio("ได้รับผลกระทบ: บาดเจ็บ", options, index=0, horizontal=True)
    with col_i2:
        house_impact = st.radio("ได้รับผลกระทบ: บ้าน", options, index=0, horizontal=True)
    with col_i3:
        asset_impact = st.radio("ได้รับผลกระทบ: ทรัพย์สิน", options, index=0, horizontal=True)

    st.markdown("---")
    st.markdown("### 2️⃣ สถานะการมาทำงาน")
    can_work = st.radio("มาทำงานได้", options, index=0, horizontal=True)
    
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        cant_work_house = st.radio("มาทำงานไม่ได้: น้ำท่วมบ้านมาไม่ได้", options, index=0, horizontal=True)
    with col_w2:
        cant_work_road = st.radio("มาทำงานไม่ได้: น้ำท่วมถนน/พื้นที่โดยรอบมาไม่ได้", options, index=0, horizontal=True)

    # ฟังก์ชันช่วยแปลงคำตอบ "ใช่" เป็น 1 และ "ไม่ใช่" เป็น 0
    def to_num(val):
        return "1" if val == "ใช่" else "0"

    col_save, col_close = st.columns([1, 1])
    with col_save:
        if st.button("💾 บันทึกข้อมูลลง Google Sheets", type="primary", use_container_width=True):
            if not faction.strip() or not dept.strip():
                st.warning("⚠️ กรุณากรอก 'ฝ่าย' และ 'แผนก'")
            else:
                try:
                    gc = get_gspread_client()
                    if gc:
                        sh = gc.open_by_key(SHEET_ID)
                        worksheet = sh.get_worksheet(0)
                        
                        # แปลงค่าจาก "ใช่/ไม่ใช่" เป็น "1/0" ก่อนบันทึก
                        new_row = [
                            faction.strip(),
                            dept.strip(),
                            group_name.strip(),
                            full_name.strip(),
                            to_num(no_impact),
                            to_num(injured),
                            to_num(house_impact),
                            to_num(asset_impact),
                            to_num(can_work),
                            to_num(cant_work_house),
                            to_num(cant_work_road)
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
    
    # แปลงคอลัมน์ตัวเลขให้เป็น int (รองรับทั้งตัวเลขสถิติเดิมและค่า 1/0)
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
