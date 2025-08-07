import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # ── 使用說明 PDF 連結 ──
    st.markdown("[📖 使用說明 (PDF)](usage_guide.pdf)")

    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    st.write("您也可以輸入目標學分，查看還差多少學分。")

    # ── 上傳檔案 ──
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
                else:
                    dfs = process_docx_file(uploaded_file)
            except Exception as e:
                st.error(f"檔案處理失敗：{e}")
                dfs = []

        if dfs:
            total_credits, passed_list, failed_list = calculate_total_credits(dfs)

            # ── 查詢結果 ──
            st.markdown("---")
            st.markdown("## ✅ 查詢結果")
            st.markdown(
                f"目前總學分: <span style='font-size:24px;'>{total_credits:.2f}</span>",
                unsafe_allow_html=True
            )

            target = st.number_input("目標學分 (例如 128)", value=128.0, min_value=0.0, step=1.0)
            diff = target - total_credits
            if diff > 0:
                st.write(f"還需 <span style='color:red;'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
            else:
                st.write(f"已超過畢業學分 <span style='color:green;'>{-diff:.2f}</span>", unsafe_allow_html=True)

            # ── 通過的課程列表 ──
            df_passed = pd.DataFrame(passed_list)
            if not df_passed.empty:
                st.markdown("---")
                st.markdown("### 📚 通過的課程列表")
                st.dataframe(
                    df_passed[["學年度","學期","科目名稱","學分","GPA"]],
                    use_container_width=True
                )
                csv_pass = df_passed.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("下載通過課程 CSV", csv_pass, file_name="passed_courses.csv")
            else:
                st.info("沒有找到任何通過的課程。")

            # ── 不及格的課程列表 ──
            df_failed = pd.DataFrame(failed_list)
            if not df_failed.empty:
                st.markdown("---")
                st.markdown("### ⚠️ 不及格的課程列表")
                st.dataframe(
                    df_failed[["學年度","學期","科目名稱","學分","GPA"]],
                    use_container_width=True
                )
                csv_fail = df_failed.to_csv(index=False, encoding="utf-8-sig")
                st.download_button("下載不及格課程 CSV", csv_fail, file_name="failed_courses.csv")
            # ── 就到這邊為止，其它程式碼完全不動 ──

            # === 新增：通識課程篩選與顯示 ===
            st.markdown("---")
            st.markdown("### 🎓 通識課程篩選")
            if df_passed.empty:
                st.info("尚未偵測到任何通過課程，無法進行通識課程篩選。")
            else:
                # 僅抓出「人文：」「自然：」「社會：」開頭的科目
                prefixes = ("人文：", "自然：", "社會：")
                mask = df_passed["科目名稱"].astype(str).str.startswith(prefixes)
                df_gened = df_passed[mask].reset_index(drop=True)

                if df_gened.empty:
                    st.info("未偵測到任何通識課程。")
                else:
                    # 新增「領域」欄：取前綴去掉「：」
                    df_gened["領域"] = df_gened["科目名稱"].str.extract(r"^(人文：|自然：|社會：)")[0].str[:-1]
                    display_cols = ["領域","學年度","學期","科目名稱","學分"]
                    st.dataframe(df_gened[display_cols], use_container_width=True)
                    # （如需下載也可再加 download_button）
            # === 通識課程篩選結束 ===

        else:
            st.warning("未從檔案中提取到任何表格數據。")
    else:
        st.info("請先上傳檔案，以開始學分計算。")

    # 回饋與開發者資訊（不受上傳檔案與否影響）
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
