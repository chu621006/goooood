import streamlit as st
import pandas as pd

from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案，工具將嘗試提取其中的表格數據並計算總學分。")

    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF, DOCX）",
        type=["pdf", "docx"]
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 依副檔名選擇處理流程
    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext == "pdf":
        extracted = process_pdf_file(uploaded_file)
    else:
        extracted = process_docx_file(uploaded_file)

    # 沒提取到任何表格
    if not extracted:
        st.error("未從檔案中提取到任何表格。請確認檔案格式＆內容，再試一次。")
        return

    # 計算學分
    total_credits, passed, failed = calculate_total_credits(extracted)

    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(f"目前總學分: <span style='font-size:24px; color:green;'>**{total_credits:.2f}**</span>", unsafe_allow_html=True)

    # 目標學分輸入
    target = st.number_input(
        "目標學分 (例如：128)",
        min_value=0.0, value=128.0, step=1.0
    )
    diff = target - total_credits
    if diff > 0:
        st.write(f"還需 <span style='font-size:20px; color:red;'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
    else:
        st.write(f"已超出目標學分 <span style='font-size:20px; color:green;'>{abs(diff):.2f}</span> 學分", unsafe_allow_html=True)

    # 通過課程列表
    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_passed = pd.DataFrame(passed)
        st.dataframe(df_passed[['學年度','學期','科目名稱','學分','GPA']], use_container_width=True)
        csv_pass = df_passed.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("下載通過課程 CSV", csv_pass, file_name="passed_courses.csv", mime="text/csv")
    else:
        st.info("沒有找到任何通過的課程。")

    # 不及格課程列表
    if failed:
        st.markdown("---")
        st.markdown("### ⚠️ 不及格的課程列表")
        df_failed = pd.DataFrame(failed)
        st.dataframe(df_failed[['學年度','學期','科目名稱','學分','GPA']], use_container_width=True)
        csv_fail = df_failed.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("下載不及格課程 CSV", csv_fail, file_name="failed_courses.csv", mime="text/csv")

    # 固定顯示：回饋 & 開發者資訊
    st.markdown("---")
    st.markdown(
        "[感謝您的使用，若您有修改建議或遇到其他問題，請點此填寫回饋表單](https://forms.gle/your-feedback-form)"
    )
    st.markdown(
        "開發者：["  
        "Chu](https://yourhomepage.example.com)",  
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
