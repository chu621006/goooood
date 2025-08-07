# app.py
import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="PDF/Word 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 使用說明連結
    st.markdown("[📑 使用說明 (PDF)](/usage_guide.pdf)")

    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader("選擇一個成績單檔案（支援 PDF, DOCX）", type=["pdf", "docx"])

    if uploaded_file is not None:
        # 根據副檔名呼叫不同的處理
        if uploaded_file.name.lower().endswith(".pdf"):
            extracted_tables = process_pdf_file(uploaded_file)
        else:
            extracted_tables = process_docx_file(uploaded_file)

        if not extracted_tables:
            st.warning("⚠️ 未從檔案中提取到任何表格。請確認檔案內容或格式是否正確。")
            return

        # 計算學分
        total_credits, calculated_courses, failed_courses = calculate_total_credits(extracted_tables)

        st.markdown("---")
        st.markdown("## ✅ 查詢結果")
        st.markdown(f"目前總學分：<span style='font-size:1.5em;'><b>{total_credits:.2f}</b></span>", unsafe_allow_html=True)

        # 目標學分
        target_credits = st.number_input(
            "目標學分 (例如：128)", 
            min_value=0.0, 
            value=128.0, 
            step=1.0
        )
        diff = target_credits - total_credits
        if diff > 0:
            st.markdown(f"還需 <span style='color:red; font-size:1.2em;'><b>{diff:.2f}</b></span> 學分", unsafe_allow_html=True)
        else:
            st.markdown(f"已超出目標學分 <span style='font-size:1.2em;'><b>{abs(diff):.2f}</b></span> 學分", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📚 通過的課程列表")
        df_passed = pd.DataFrame(calculated_courses)
        if df_passed.empty:
            st.info("沒有找到任何通過的課程。")
        else:
            st.dataframe(df_passed[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)

            # 下載通過課程 CSV（Big5/CP950 編碼）
            csv_pass = df_passed.to_csv(index=False, encoding='cp950', errors='replace')
            st.download_button(
                label="下載通過課程 CSV",
                data=csv_pass,
                file_name=f"{uploaded_file.name.rsplit('.',1)[0]}_通過課程.csv",
                mime="text/csv",
                key="download_passed_btn"
            )

        st.markdown("---")
        st.markdown("⚠️ 不及格的課程列表")
        df_failed = pd.DataFrame(failed_courses)
        if df_failed.empty:
            st.info("沒有找到任何不及格的課程。")
        else:
            st.dataframe(df_failed[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)

            # 下載不及格課程 CSV（Big5/CP950 編碼）
            csv_fail = df_failed.to_csv(index=False, encoding='cp950', errors='replace')
            st.download_button(
                label="下載不及格課程 CSV",
                data=csv_fail,
                file_name=f"{uploaded_file.name.rsplit('.',1)[0]}_不及格課程.csv",
                mime="text/csv",
                key="download_failed_btn"
            )

        # 回饋＆開發者資訊（固定顯示）
        st.markdown("---")
        st.markdown(
            "感謝您的使用，若您有相關修改建議或發生其他錯誤，"
            "[請點此填寫意見回饋表單](https://your-feedback-form.url)"
        )
        st.markdown(
            "開發者："
            "[Chu](https://your-profile.url)  |  "
            "GitHub：[@你的帳號](https://github.com/你的帳號)"
        )

if __name__ == "__main__":
    main()
