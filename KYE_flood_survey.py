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

    total_employees = len(df_data)

    if total_employees > 0:
        # ---------------------------------------------------------
        # 1️⃣ คำนวณสถานะการได้รับผลกระทบและการมาทำงานแบบรายบุคคล (ไม่นับซ้ำ)
        # ---------------------------------------------------------
        # พนักงานที่มาทำงานไม่ได้ = มีการเลือกสาเหตุมาไม่ได้อย่างน้อย 1 ข้อ
        df_data["มาทำงานไม่ได้_count"] = (
            (df_data["มาทำงานไม่ได้: น้ำท่วมบ้านมาไม่ได้"] == 1) | 
            (df_data["มาทำงานไม่ได้: น้ำท่วมถนน พื้นที่โดยรอบมาไม่ได้"] == 1)
        ).astype(int)
        
        # พนักงานที่มาทำงานได้ = ไม่ได้เลือกมาทำงานไม่ได้
        df_data["มาทำงานได้_count"] = (df_data["มาทำงานไม่ได้_count"] == 0).astype(int)

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
        # 📋 ตารางสรุปภาพรวมแยกตาม "ฝ่าย" (เฉพาะการมาทำงาน)
        # ---------------------------------------------------------
        st.markdown("### 🧮 ยอดรวมการมาทำงานแยกตามฝ่าย")

        # Groupby ตามคอลัมน์ "ฝ่าย"
        df_faction = df_data.groupby("ฝ่าย").agg(
            can_work=("มาทำงานได้_count", "sum"),
            cant_work=("มาทำงานไม่ได้_count", "sum"),
            total_emp=("ชื่อ-นามสกุล", "count")
        ).reset_index()

        # คำนวณสัดส่วน %
        df_faction["มาทำงานได้ (คน)"] = df_faction["can_work"].astype(str) + " คน"
        df_faction["มาทำงานได้ (%)"] = (df_faction["can_work"] / df_faction["total_emp"] * 100).map("{:.1f}%".format)
        
        df_faction["มาทำงานไม่ได้ (คน)"] = df_faction["cant_work"].astype(str) + " คน"
        df_faction["มาทำงานไม่ได้ (%)"] = (df_faction["cant_work"] / df_faction["total_emp"] * 100).map("{:.1f}%".format)
        
        df_faction["รวมทั้งหมด (คน)"] = df_faction["total_emp"].astype(str) + " คน"
        df_faction["คิดเป็น % ของผลรวมทั้งหมด"] = (df_faction["total_emp"] / total_employees * 100).map("{:.1f}%".format)

        # จัดคอลัมน์ที่จะแสดงผล
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

        # สร้างแถว Total สรุปรวมทุกฝ่าย
        total_faction_row = pd.DataFrame([{
            "ฝ่าย": "รวมทั้งหมด (Total)",
            "มาทำงานได้ (คน)": f"{can_work_count} คน",
            "มาทำงานได้ (%)": f"{can_work_pct:.1f}%",
            "มาทำงานไม่ได้ (คน)": f"{cant_work_count} คน",
            "มาทำงานไม่ได้ (%)": f"{cant_work_pct:.1f}%",
            "รวมทั้งหมด (คน)": f"{total_employees} คน",
            "คิดเป็น % ของผลรวมทั้งหมด": "100.0%"
        }])

        # รวมตารางสรุปรายฝ่ายเข้ากับแถว Grand Total
        df_faction_final = pd.concat([df_faction_display, total_faction_row], ignore_index=True)

        st.dataframe(df_faction_final, use_container_width=True, hide_index=True)

else:
    st.info("ℹ️ ยังไม่มีข้อมูลในระบบ หรือยังไม่ได้ตั้งค่า `SHEET_ID` ในไฟล์")
