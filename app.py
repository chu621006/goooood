# app.py
import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 使用說明連結（PDF）
    st.markdown(
        "[📘 使用說明 (PDF)](usage_guide.pdf)",
        unsafe_allow_html=True
    )

    st.markdown("請上傳 PDF（純表格）或 Word（.docx）格式的成績單檔案。")

    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF, DOCX）",
        type=["pdf", "docx"]
    )
    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 1. 解析檔案
    if uploaded_file.name.lower().endswith(".docx"):
        dfs = process_docx_file(uploaded_file)
    else:
        dfs = process_pdf_file(uploaded_file)

    # 2. 計算學分
    total_credits, passed, failed = calculate_total_credits(dfs)

    # 3. 顯示查詢結果
    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(
        f"**目前總學分：** <span style='font-size:2rem;color:green;'>{total_credits:.2f}</span>",
        unsafe_allow_html=True
    )
    target = st.number_input(
        "目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0
    )
    diff = target - total_credits
    if diff > 0:
        st.write(
            f"還需 <span style='color:red;'>{diff:.2f}</span> 學分",
            unsafe_allow_html=True
        )
    else:
        st.write(
            f"已超越畢業學分 <span style='color:green;'>{abs(diff):.2f}</span>",
            unsafe_allow_html=True
        )

    # 4. 通過課程列表
    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_pass = pd.DataFrame(passed)
        st.dataframe(
            df_pass[["學年度","學期","科目名稱","學分","GPA"]],
            use_container_width=True
        )
        csv_p = df_pass.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "下載通過課程 CSV",
            csv_p,
            file_name="passed_courses.csv",
            mime="text/csv"
        )
    else:
        st.info("沒有找到任何通過的課程。")

    # 5. 不及格課程列表
    if failed:
        st.markdown("---")
        st.markdown("### ⚠️ 不及格的課程列表")
        df_fail = pd.DataFrame(failed)
        st.dataframe(
            df_fail[["學年度","學期","科目名稱","學分","GPA"]],
            use_container_width=True
        )
        csv_f = df_fail.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "下載不及格課程 CSV",
            csv_f,
            file_name="failed_courses.csv",
            mime="text/csv"
        )

    # 6. 通識課程統計
    GE_PREFIXES = ["人文：", "自然：", "社會："]
    ge_courses = []
    for c in passed:
        name = c["科目名稱"]
        for pre in GE_PREFIXES:
            if name.startswith(pre):
                ge_courses.append({
                    **c,
                    "領域": pre[:-1]  # 「人文：」→「人文」
                })
                break

    total_ge = sum(c["學分"] for c in ge_courses)
    ge_by_domain = {dom: 0.0 for dom in ["人文", "自然", "社會"]}
    for c in ge_courses:
        ge_by_domain[c["領域"]] += c["學分"]

    st.markdown("---")
    st.markdown("## 🎓 通識課程統計")
    st.write(f"- **總計通識學分：** {total_ge:.2f} 學分")
    st.write(f"- 人文：{ge_by_domain['人文']:.2f} 學分")
    st.write(f"- 自然：{ge_by_domain['自然']:.2f} 學分")
    st.write(f"- 社會：{ge_by_domain['社會']:.2f} 學分")
    if ge_courses:
        df_ge = pd.DataFrame(ge_courses)[["領域","學年度","學期","科目名稱","學分"]]
        st.dataframe(df_ge, use_container_width=True)
    else:
        st.info("沒有符合條件的通識課程。")

    # 7. 回饋 & 開發者資訊（永遠顯示在最底部）
    st.markdown("---")
    st.markdown(
        "[📝 感謝您的使用，若您有建議或遇到問題，請點此填寫回饋表單](https://docs.google.com/forms/your-form)",
        unsafe_allow_html=True
    )
    st.markdown(
        "開發者："
        "[Chu](https://your-homepage.example.com)",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
