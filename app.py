import streamlit as st
import pandas as pd
# … 你原本的 import 保持不動 …

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # --- 新增：先讓使用者可以上傳已下載的「通過課程 CSV」 ---
    csv_file = st.file_uploader(
        "📝（選用）若已下載「通過課程 CSV」，可直接上傳以做通識課統計。",
        type=["csv"],
        key="upload_passed_csv"
    )

    if csv_file is not None:
        # 直接讀 CSV，並假設它就是 df_passed
        try:
            df_passed = pd.read_csv(csv_file)
            use_csv = True
        except Exception as e:
            st.error(f"CSV 讀取失敗：{e}")
            return
    else:
        use_csv = False

    # --- 下面走你原本的 PDF / DOCX 處理流程 ---
    if not use_csv:
        uploaded_file = st.file_uploader(
            "請上傳 PDF（純表格）或 Word（.docx）格式的成績單檔案（支援 PDF, DOCX）",
            type=["pdf", "docx"]
        )
        if uploaded_file is None:
            st.info("請先上傳檔案，以開始學分計算。")
            return

        # 你的解析程式：PDF / DOCX 分別呼叫 process_pdf_file / process_docx_file
        if uploaded_file.name.lower().endswith(".pdf"):
            extracted = process_pdf_file(uploaded_file)
        else:
            extracted = process_docx_file(uploaded_file)

        total_credits, calculated_courses, failed_courses = calculate_total_credits(extracted)
        # 把計算結果轉成 DataFrame
        df_passed = pd.DataFrame(calculated_courses)
        df_failed = pd.DataFrame(failed_courses)

        # （接著是你原本顯示結果、下載 CSV 的程式碼）
        # …
        # 下載通過課程
        if not df_passed.empty:
            csv_passed = df_passed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載通過課程 CSV", csv_passed, "passed_courses.csv", "text/csv")
        # 下載不及格課程
        if not df_failed.empty:
            csv_failed = df_failed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載不及格課程 CSV", csv_failed, "failed_courses.csv", "text/csv")

    # 到這裡，df_passed 已經就緒──要麼來自上傳的 CSV，要麼是剛解析出來的結果

    # … 你原本顯示「通過課程列表」的程式碼 …


    # —— 通識課程統計 —— #
    st.markdown("### 🎓 通識課程統計")
    if not df_passed.empty and "科目名稱" in df_passed.columns:
        prefixes = ("人文：", "自然：", "社會：")
        mask = df_passed["科目名稱"].str.startswith(prefixes, na=False)
        df_gen_ed = df_passed[mask]
        if not df_gen_ed.empty:
            wanted = ["學年度", "學期", "科目名稱", "學分"]
            cols = [c for c in wanted if c in df_gen_ed.columns]
            st.dataframe(df_gen_ed[cols], use_container_width=True)
        else:
            st.info("未偵測到任何通識課程。")
    else:
        st.info("未偵測到任何通識課程。")
    # —— 通識課程統計 結束 —— #


if __name__ == "__main__":
    main()
