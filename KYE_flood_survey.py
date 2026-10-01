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

    # แสดงตารางข้อมูลรายละเอียดการตอบแบบสำรวจ
    st.dataframe(df_data, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 📊 สรุปภาพรวมองค์กร (Executive Summary)")

    # จำนวนพนักงานทั้งหมดที่ตอบแบบสำรวจ (คิดตามรายชื่อ/แถว)
    total_employees = len(df_data)

    if total_employees > 0:
        # ---------------------------------------------------------
        # 1️⃣ สรุปการได้รับผลกระทบ (นับพนักงานแบบรายคน)
        # ---------------------------------------------------------
        # พนักงานที่ได้รับผลกระทบ = มีการเลือก "กระทบ" หรือเลือกผลกระทบย่อยอย่างน้อย 1 ข้อ
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

        # ---------------------------------------------------------
        # 2️⃣ สรุปสถานะการมาทำงาน (นับพนักงานแบบรายคน)
        # ---------------------------------------------------------
        # พนักงานที่มาทำงานไม่ได้ = มีการเลือกสาเหตุมาไม่ได้อย่างน้อย 1 ข้อ
        cant_work_mask = (
            (df_data["มาทำงานไม่ได้: น้ำท่วมบ้านมาไม่ได้"] == 1) | 
            (df_data["มาทำงานไม่ได้: น้ำท่วมถนน พื้นที่โดยรอบมาไม่ได้"] == 1)
        )
        cant_work_count = int(cant_work_mask.sum())
        can_work_count = total_employees - cant_work_count

        can_work_pct = (can_work_count / total_employees) * 100
        cant_work_pct = (cant_work_count / total_employees) * 100

        # ---------------------------------------------------------
        # 🖥️ แสดงผลสรุปด้วย Metric Cards
        # ---------------------------------------------------------
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
        
        # ---------------------------------------------------------
        # 📋 ตารางสรุปภาพรวมในรูปแบบตารางตัวเลขและเปอร์เซ็นต์
        # ---------------------------------------------------------
        st.markdown("#### 🧮 ตารางสรุปสัดส่วนภาพรวมองค์กร")
        
        summary_table_data = [
            {
                "หัวข้อแบบสำรวจ": "1. การได้รับผลกระทบจากน้ำท่วม",
                "กลุ่มที่ 1 (คน)": f"ได้รับผลกระทบ: {affected_count} คน",
                "สัดส่วนกลุ่มที่ 1 (%)": f"{affected_pct:.2f}%",
                "กลุ่มที่ 2 (คน)": f"ไม่ได้รับผลกระทบ: {not_affected_count} คน",
                "สัดส่วนกลุ่มที่ 2 (%)": f"{not_affected_pct:.2f}%",
                "รวมพนักงานทั้งหมด (คน)": f"{total_employees} คน",
                "รวมสัดส่วน (%)": "100.00%"
            },
            {
                "หัวข้อแบบสำรวจ": "2. สถานะการมาทำงาน",
                "กลุ่มที่ 1 (คน)": f"มาทำงานได้: {can_work_count} คน",
                "สัดส่วนกลุ่มที่ 1 (%)": f"{can_work_pct:.2f}%",
                "กลุ่มที่ 2 (คน)": f"มาทำงานไม่ได้: {cant_work_count} คน",
                "สัดส่วนกลุ่มที่ 2 (%)": f"{cant_work_pct:.2f}%",
                "รวมพนักงานทั้งหมด (คน)": f"{total_employees} คน",
                "รวมสัดส่วน (%)": "100.00%"
            }
        ]

        df_summary_table = pd.DataFrame(summary_table_data)
        st.dataframe(df_summary_table, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 🧮 ยอดรวมการเลือกตอบแยกตามหัวข้อย่อย (ฝ่าย / แผนก)")
        
        # ตารางสรุปจำนวนการเลือกตอบหัวข้อย่อยรวม
        df_by_faction = df_data.groupby("ฝ่าย", as_index=False)[num_cols].sum()
        df_by_faction["แผนก"] = "รวมตามฝ่าย"
        df_by_faction["กลุ่ม"] = "-"
        df_by_faction["ชื่อ-นามสกุล"] = "-"
        df_by_faction = df_by_faction[COLUMNS]

        total_row = {
            "ฝ่าย": "รวมรายการเลือกตอบทั้งหมด", 
            "แผนก": "-", 
            "กลุ่ม": "-", 
            "ชื่อ-นามสกุล": "-"
        }
        for col in num_cols:
            total_row[col] = df_data[col].sum()
        
        df_grand_total = pd.DataFrame([total_row])[COLUMNS]
        df_total_summary = pd.concat([df_by_faction, df_grand_total], ignore_index=True)
        
        st.dataframe(df_total_summary, use_container_width=True, hide_index=True)

else:
    st.info("ℹ️ ยังไม่มีข้อมูลในระบบ หรือยังไม่ได้ตั้งค่า `SHEET_ID` ในไฟล์")
