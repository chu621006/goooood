import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

# --- 通識前綴與中文對應 ---
GE_PREFIXES = {
    "人文：": "人文",
    "自然：": "自然",
    "社會：": "社會",
}

def summarize_ge(courses):
    """
    根據課程名稱前綴，統計通識課程總學分、各領域學分與課程清單。
    courses: list of dict, 每項 dict 包含 '科目名稱', '學分', ...
    """
    total = 0.0
    per_domain = {v: 0.0 for v in GE_PREFIXES.values()}
    included = []

    for c in courses:
        name = c["科目名稱"]
        credit = c["學分"]
        for prefix, domain in GE_PREFIXES.items():
            if name.startswith(prefix):
                total += credit
                per_domain[domain] += credit
                included.append(c)
                break

    return total, per_domain, included

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    uploaded_file = st.file_uploader("選擇成績單檔案（支援 PDF, DOCX）", type=["pdf", "docx"])
    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 1. 依副檔名呼叫不同處理
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "pdf":
        dfs = process_pdf_file(uploaded_file)
    else:
        dfs = process_docx_file(uploaded_file)

    # 2. 主計算
    total_credits, passed, failed = calculate_total_credits(dfs)

    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(
        f"<span style='font-size:28px;'>目前總學分: <strong>{total_credits:.2f}</strong></span>", 
        unsafe_allow_html=True
    )
    # 距離畢業學分
    target = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target - total_credits
    diff_color = "red" if diff>0 else "green"
    st.markdown(
        f"<span style='font-size:20px;'>還需 <span style='color:{diff_color};'>{diff:.2f}</span> 學分</span>",
        unsafe_allow_html=True
    )

    # 3. 通過 & 不及格列表
    st.markdown("---")
    st.subheader("📚 通過的課程列表")
    if passed:
        df_pass = pd.DataFrame(passed)
        st.dataframe(df_pass[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
    else:
        st.info("沒有找到可以計算學分的科目。")

    if failed:
        st.markdown("---")
        st.subheader("⚠️ 不及格的課程列表")
        df_fail = pd.DataFrame(failed)
        st.dataframe(df_fail[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
        st.info("這些科目因成績不及格未計入總學分。")

    # 4. **新增**：通識課程統計
    st.markdown("---")
    st.subheader("🎓 通識課程學分統計")
    ge_total, ge_per, ge_list = summarize_ge(passed)
    st.markdown(f"- **通識總學分**：{ge_total:.2f} 學分")
    for domain, cred in ge_per.items():
        st.markdown(f"  - **{domain}**：{cred:.2f} 學分")
    if ge_list:
        st.markdown("**列入通識計算之課程**：")
        df_ge = pd.DataFrame(ge_list)
        st.dataframe(df_ge[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
    else:
        st.info("未偵測到符合前綴之通識課程。")

    # 5. 下載按鈕
    if passed:
        csv_pass = pd.DataFrame(passed).to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載通過課程 CSV", csv_pass, file_name="passed_courses.csv", mime="text/csv")
    if failed:
        csv_fail = pd.DataFrame(failed).to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載不及格課程 CSV", csv_fail, file_name="failed_courses.csv", mime="text/csv")

if __name__ == "__main__":
    main()
