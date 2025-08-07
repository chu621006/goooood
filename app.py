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
    st.markdown("[📘 使用說明 (PDF)](usage_guide.pdf)", unsafe_allow_html=True)

    st.markdown("請上傳 PDF（純表格）或 Word（.docx）格式的成績單檔案。")
    uploaded_file = st.file_uploader("選擇檔案（PDF, DOCX）", type=["pdf","docx"])
    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 解析檔案
    if uploaded_file.name.lower().endswith(".docx"):
        dfs = process_docx_file(uploaded_file)
    else:
        dfs = process_pdf_file(uploaded_file)

    # 計算學分
    total_credits, passed, failed = calculate_total_credits(dfs)

    # 查詢結果
    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(
        f"**目前總學分：** <span style='font-size:2rem;color:green;'>{total_credits:.2f}</span>",
        unsafe_allow_html=True
    )
    target = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target - total_credits
    if diff > 0:
        st.write(f"還需 <span style='color:red;'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
    else:
        st.write(f"已超越畢業學分 <span style='color:green;'>{abs(diff):.2f}</span>", unsafe_allow_html=True)

    # 通過的課程列表
    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_pass = pd.DataFrame(passed)
        # 只顯示真正有的欄位，避免 KeyError
        want = ["學年度","學期","科目名稱","學分","GPA"]
        cols = [c for c in want if c in df_pass.columns]
        st.dataframe(df_pass[cols], use_container_width=True)
        csv_p = df_pass.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載通過課程 CSV", csv_p, "passed.csv", "text/csv")
    else:
        st.info("沒有找到通過的課程。")

    # 不及格的課程列表
    if failed:
        st.markdown("---")
        st.markdown("### ⚠️ 不及格的課程列表")
        df_fail = pd.DataFrame(failed)
        want = ["學年度","學期","科目名稱","學分","GPA"]
        cols = [c for c in want if c in df_fail.columns]
        st.dataframe(df_fail[cols], use_container_width=True)
        csv_f = df_fail.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載不及格課程 CSV", csv_f, "failed.csv", "text/csv")

    # 通識課程統計
    GE_PREFIXES = ["人文：","自然：","社會："]
    ge = []
    for c in passed:
        name = c.get("科目名稱","")
        for pre in GE_PREFIXES:
            if name.startswith(pre):
                ge.append({**c, "領域":pre[:-1]})
                break
    total_ge = sum(x["學分"] for x in ge)
    ge_dom = {d:0.0 for d in ["人文","自然","社會"]}
    for x in ge:
        ge_dom[x["領域"]] += x["學分"]

    st.markdown("---")
    st.markdown("## 🎓 通識課程統計")
    st.write(f"- **總計通識學分：** {total_ge:.2f} 學分")
    st.write(f"- 人文：{ge_dom['人文']:.2f} 學分")
    st.write(f"- 自然：{ge_dom['自然']:.2f} 學分")
    st.write(f"- 社會：{ge_dom['社會']:.2f} 學分")
    if ge:
        df_ge = pd.DataFrame(ge)[["領域","學年度","學期","科目名稱","學分"]]
        st.dataframe(df_ge, use_container_width=True)
    else:
        st.info("沒有符合條件的通識課程。")

    # 回饋＆開發者資訊（永遠顯示）
    st.markdown("---")
    st.markdown("[📝 感謝您的使用，若您有建議或遇到問題，請填寫回饋表單](https://docs.google.com/forms/your-form)", unsafe_allow_html=True)
    st.markdown("開發者： [Chu](https://your-homepage.example.com)", unsafe_allow_html=True)

if __name__=="__main__":
    main()
