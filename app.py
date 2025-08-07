import streamlit as st
import pandas as pd

# 新增這三行，確保後面能呼叫到解析與計算函式
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 使用說明超連結
    st.markdown("[📖 使用說明 (PDF)](usage_guide.pdf)")

    # --- (1) 選擇性：先上傳已下載的「通過課程 CSV」 --- #
    csv_file = st.file_uploader(
        "📝（選用）若已下載「通過課程 CSV」，可直接上傳以做通識課統計。",
        type=["csv"],
        key="upload_passed_csv"
    )
    if csv_file is not None:
        try:
            df_passed = pd.read_csv(csv_file)
            use_csv = True
        except Exception as e:
            st.error(f"CSV 讀取失敗：{e}")
            return
    else:
        use_csv = False

    # --- (2) 若沒上 CSV，就走 PDF / DOCX 解析原流程 --- #
    if not use_csv:
        uploaded_file = st.file_uploader(
            "請上傳 PDF（純表格）或 Word（.docx）格式的成績單檔案（支援 PDF, DOCX）",
            type=["pdf", "docx"]
        )
        if uploaded_file is None:
            st.info("請先上傳檔案，以開始學分計算。")
            return

        # PDF or DOCX 解析
        if uploaded_file.name.lower().endswith(".pdf"):
            extracted = process_pdf_file(uploaded_file)
        else:
            extracted = process_docx_file(uploaded_file)

        total_credits, passed, failed = calculate_total_credits(extracted)
        df_passed = pd.DataFrame(passed)
        df_failed = pd.DataFrame(failed)

        # --- 顯示總學分、目標學分、差額 --- #
        st.markdown("---")
        st.markdown("## ✅ 查詢結果")
        st.markdown(f"目前總學分: <span style='font-size:24px; font-weight:600;'>{total_credits:.2f}</span>", unsafe_allow_html=True)

        target_credits = st.number_input(
            "目標學分 (例如：128)",
            min_value=0.0, value=128.0, step=1.0
        )
        diff = target_credits - total_credits
        if diff > 0:
            st.markdown(f"還需 <span style='color:red; font-weight:600;'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
        elif diff < 0:
            st.success(f"已超出 {abs(diff):.2f} 學分")
        else:
            st.success("正好達標！")

        # --- 顯示「通過的課程列表」與下載按鈕 --- #
        st.markdown("---")
        st.markdown("### 📚 通過的課程列表")
        if not df_passed.empty:
            cols = [c for c in ["學年度","學期","科目名稱","學分","GPA"] if c in df_passed.columns]
            st.dataframe(df_passed[cols], use_container_width=True)
            csv_data = df_passed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載通過課程 CSV", data=csv_data,
                               file_name="passed_courses.csv", mime="text/csv")
        else:
            st.info("沒有找到任何通過課程。")

        # --- 顯示「不及格的課程列表」與下載按鈕 --- #
        if not df_failed.empty:
            st.markdown("---")
            st.markdown("### ⚠️ 不及格的課程列表")
            cols_f = [c for c in ["學年度","學期","科目名稱","學分","GPA"] if c in df_failed.columns]
            st.dataframe(df_failed[cols_f], use_container_width=True)
            csv_data_f = df_failed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載不及格課程 CSV", data=csv_data_f,
                               file_name="failed_courses.csv", mime="text/csv")

    # --- (3) 通識課程統計（一定有 df_passed） --- #
    st.markdown("---")
    st.markdown("### 🎓 通識課程統計")
    if not df_passed.empty and "科目名稱" in df_passed.columns:
        prefixes = ("人文：", "自然：", "社會：")
        mask = df_passed["科目名稱"].str.startswith(prefixes, na=False)
        df_gen_ed = df_passed[mask]
        if not df_gen_ed.empty:
            cols_g = [c for c in ("學年度","學期","科目名稱","學分") if c in df_gen_ed.columns]
            st.dataframe(df_gen_ed[cols_g], use_container_width=True)
        else:
            st.info("未偵測到任何通識課程。")
    else:
        st.info("未偵測到任何通識課程。")

    # --- (4) 回饋表單 & 開發者資訊（始終顯示在最底）--- #
    st.markdown("---")
    st.markdown(
        "[🙏 感謝您的使用，若有修改建議或其他錯誤，請點此填寫回饋表單]"
        "(https://forms.gle/YourFeedbackForm)")
    st.markdown(
        "開發者："
        "[Chu](https://yourhomepage.example.com)",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
