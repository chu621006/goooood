# app.py
import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # --- 使用說明 PDF 連結 ---
    st.markdown("[📖 使用說明 (PDF)](usage_guide.pdf)")

    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    st.write("您也可以輸入目標學分，查看還差多少學分。")

    # --- 檔案上傳 & 解析 ---
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案 (支援 PDF, DOCX)", 
        type=["pdf", "docx"]
    )

    df_passed = pd.DataFrame()
    df_failed = pd.DataFrame()

    if uploaded_file:
        filename = uploaded_file.name.lower()
        with st.spinner("正在處理檔案…"):
            try:
                if filename.endswith(".pdf"):
                    dfs = process_pdf_file(uploaded_file)
                else:  # docx
                    dfs = process_docx_file(uploaded_file)
            except Exception as e:
                st.error(f"檔案處理失敗：{e}")
                dfs = []

        if dfs:
            total_credits, passed_list, failed_list = calculate_total_credits(dfs)

            # --- 顯示總學分 & 目標學分差距 ---
            st.markdown("---")
            st.markdown("## ✅ 查詢結果")
            st.markdown(f"目前總學分: <span style='font-size:24px;'>{total_credits:.2f}</span>", unsafe_allow_html=True)

            target = st.number_input("目標學分 (例如 128)", value=128.0, min_value=0.0, step=1.0)
            diff = target - total_credits
            if diff > 0:
                st.write(f"還需 <span style='color:red;'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
            else:
                st.write(f"已超過畢業學分 <span style='color:green;'>{-diff:.2f}</span>", unsafe_allow_html=True)

            # --- 通過課程列表 ---
            df_passed = pd.DataFrame(passed_list)
            if not df_passed.empty:
                st.markdown("---")
                st.markdown("### 📚 通過的課程列表")
                st.dataframe(df_passed[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
                csv_pass = df_passed.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("下載通過課程 CSV", csv_pass, file_name="passed_courses.csv")
            else:
                st.info("沒有找到任何通過的課程。")

            # --- 不及格課程列表 ---
            df_failed = pd.DataFrame(failed_list)
            if not df_failed.empty:
                st.markdown("---")
                st.markdown("### ⚠️ 不及格的課程列表")
                st.dataframe(df_failed[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
                csv_fail = df_failed.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("下載不及格課程 CSV", csv_fail, file_name="failed_courses.csv")
        else:
            st.warning("未從檔案中提取到任何表格數據。")

    else:
        st.info("請先上傳檔案，以開始學分計算。")

    # --- 可選：上傳通過課程 CSV 來做通識統計 ---
    st.markdown("---")
    st.markdown("📑 （選用）若已下載「通過課程 CSV」，可直接上傳以做通識課程統計。")
    csv_file = st.file_uploader("上傳通過課程 CSV", type=["csv"], key="gen_ed_csv")
    df_gen_ed = pd.DataFrame()
    if csv_file:
        try:
            df_gen_ed = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"CSV 讀取失敗：{e}")

    # --- 🎓 通識課程統計 ---
    st.markdown("---")
    st.markdown("### 🎓 通識課程統計")

    # 優先用 CSV，否則用原本計算出來的 df_passed
    source_df = df_gen_ed if not df_gen_ed.empty else df_passed.copy()
    if "科目名稱" not in source_df.columns:
        st.info("尚未取得任何通過課程，無法進行通識課程統計。")
    else:
        prefixes = ("人文：", "自然：", "社會：")
        mask = source_df["科目名稱"].astype(str).str.startswith(prefixes)
        df_ed = source_df[mask].reset_index(drop=True)
        if df_ed.empty:
            st.info("未偵測到任何通識課程。")
        else:
            # 補「領域」欄
            if "領域" not in df_ed.columns:
                df_ed["領域"] = df_ed["科目名稱"].str.extract(r"^(人文：|自然：|社會：)")[0].str[:-1]
            cols = [c for c in ["領域","學年度","學期","科目名稱","學分"] if c in df_ed.columns]
            st.dataframe(df_ed[cols], use_container_width=True)
            # CSV 下載
            ed_csv = df_ed[cols].to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載通識課程 CSV", ed_csv, file_name="gen_ed_courses.csv")

    # --- 回饋 & 開發者資訊 ---
    st.markdown("---")
    st.markdown(
        "感謝您的使用，若您有相關修改建議或發生其他類型錯誤，"
        "[請點此填寫回饋表單](https://your-feedback-form.example.com)"
    )
    st.markdown(
        "開發者："
        "[Chu](https://your-profile-or-homepage.example.com)"
    )

if __name__ == "__main__":
    main()
