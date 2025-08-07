import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # --- 上傳檔案 ---
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader("選擇一個成績單檔案（支援 PDF, DOCX）", type=["pdf", "docx"])
    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # --- 解析檔案 ---
    if uploaded_file.type == "application/pdf":
        extracted = process_pdf_file(uploaded_file)
    else:
        extracted = process_docx_file(uploaded_file)

    # --- 計算學分 ---
    total_credits, passed_list, failed_list = calculate_total_credits(extracted)

    # **關鍵修正**：把 list 轉成 DataFrame
    df_passed = pd.DataFrame(passed_list)
    df_failed = pd.DataFrame(failed_list)

    # --- 顯示查詢結果 ---
    st.markdown("---")
    st.subheader("✅ 查詢結果")
    st.markdown(f"目前總學分：**{total_credits:.2f}**")

    target_credits = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target_credits - total_credits
    if diff > 0:
        st.write(f"還需 **:red[{diff:.2f}]** 學分", unsafe_allow_html=True)
    else:
        st.write(f"已超出目標 **{abs(diff):.2f}** 學分")

    # --- 顯示通過的課程 & 下載 CSV ---
    st.markdown("---")
    st.subheader("📚 通過的課程列表")
    if df_passed.empty:
        st.info("沒有找到可計算學分的通過科目。")
    else:
        st.dataframe(df_passed, use_container_width=True)
        csv_pass = df_passed.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載通過課程 CSV", csv_pass, file_name="passed_courses.csv", mime="text/csv")

    # --- 顯示不及格的課程 & 下載 CSV ---
    if not df_failed.empty:
        st.markdown("---")
        st.subheader("⚠️ 不及格的課程列表")
        st.dataframe(df_failed, use_container_width=True)
        csv_fail = df_failed.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載不及格課程 CSV", csv_fail, file_name="failed_courses.csv", mime="text/csv")

    # --- 通識課程篩選 ---
    st.markdown("---")
    st.markdown("### 🎓 通識課程篩選")

    if df_passed.empty:
        st.info("尚未偵測到任何通過課程，無法進行通識課程篩選。")
    else:
        # 動態尋找「科目名稱」欄位
        subj_cols = [c for c in df_passed.columns if "科目" in c]
        if not subj_cols:
            st.error("找不到任何「科目名稱」欄位，無法篩選通識課程。")
        else:
            subj_col = subj_cols[0]
            # 去除所有空白
            df_passed["__subj_clean"] = (
                df_passed[subj_col].astype(str).str.replace(r"\s+", "", regex=True)
            )
            # 用正則匹配前綴
            mask = df_passed["__subj_clean"].str.contains(r"^(人文|自然|社會)[:：]")
            df_gened = df_passed[mask].copy()

            if df_gened.empty:
                st.info("未偵測到任何通識課程。")
            else:
                df_gened["領域"] = (
                    df_gened["__subj_clean"].str.extract(r"^(人文|自然|社會)[:：]")[0]
                )
                show_cols = ["領域"] + [
                    c for c in ["學年度","學期", subj_col, "學分"] if c in df_gened.columns
                ]
                st.dataframe(df_gened[show_cols].reset_index(drop=True), use_container_width=True)

    # --- 回饋＆開發者資訊（固定顯示） ---
    st.markdown("---")
    st.markdown(
        '[💬 感謝您的使用，若您有修改建議或遇到其他錯誤，請點我填寫回饋表單](https://你的回饋表單網址)'
    )
    st.markdown(
        '開發者：'
        '[Chu](https://你的個人連結)', unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
