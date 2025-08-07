import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # --- 上傳檔案 ---
    uploaded_file = st.file_uploader(
        "請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。",
        type=["pdf","docx"]
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # --- 先依副檔名分流 ---
    if uploaded_file.name.lower().endswith(".pdf"):
        extracted = process_pdf_file(uploaded_file)
    else:
        extracted = process_docx_file(uploaded_file)

    total_credits, calculated_courses, failed_courses = calculate_total_credits(extracted)

    # --- 顯示結果 ---
    st.markdown("---")
    st.subheader("✅ 查詢結果")
    st.markdown(f"**目前總學分：** {total_credits:.2f}")
    target = st.number_input("目標學分 (例如 128)", value=128.0, step=1.0)
    diff = target - total_credits
    if diff > 0:
        st.write(f"還需 **{diff:.2f}** 學分")
    else:
        st.write(f"已超出 **{abs(diff):.2f}** 學分")

    # --- 通過課程表 ---
    st.markdown("---")
    st.subheader("📚 通過的課程列表")
    df_passed = pd.DataFrame(calculated_courses)
    if df_passed.empty:
        st.info("沒有找到任何通過的課程。")
    else:
        st.dataframe(df_passed[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
        csv_pass = df_passed.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載通過課程 CSV", csv_pass, "passed_courses.csv", "text/csv")

    # --- 不及格課程表 ---
    st.markdown("---")
    st.subheader("⚠️ 不及格的課程列表")
    df_failed = pd.DataFrame(failed_courses)
    if df_failed.empty:
        st.info("沒有不及格的課程。")
    else:
        st.dataframe(df_failed[["學年度","學期","科目名稱","學分","GPA"]], use_container_width=True)
        csv_fail = df_failed.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載不及格課程 CSV", csv_fail, "failed_courses.csv", "text/csv")

    # === 下面開始：通識課程篩選（確保 df_passed 已定義） ===
    st.markdown("---")
    st.subheader("🎓 通識課程篩選")

    # 若 df_passed.empty，代表根本沒有任何通過課程
    if df_passed.empty:
        st.info("尚未偵測到任何通過課程，無法進行通識課程篩選。")

    # 再檢查「科目名稱」欄位是否存在
    elif "科目名稱" not in df_passed.columns:
        st.error("無法找到「科目名稱」欄，無法進行通識課程篩選。")

    else:
        # 1) 先去除所有空白字元，讓後續比對更健壯
        names = (
            df_passed["科目名稱"]
            .astype(str)
            .str.replace(r"\s+", "", regex=True)
        )
        # 2) 定義正則：支援全形或半形冒號
        pattern = r"^(人文|自然|社會)[:：]"

        # 建立篩選遮罩
        mask = names.str.match(pattern)
        df_gened = df_passed[mask].copy()

        if df_gened.empty:
            st.info("未偵測到任何通識課程。")
        else:
            # 萃取「領域」欄：人文 / 自然 / 社會
            df_gened["領域"] = names[mask].str.extract(pattern)[0]

            # 只顯示我們想要的幾個欄位
            desired = ["領域", "學年度", "學期", "科目名稱", "學分"]
            cols = [c for c in desired if c in df_gened.columns]
            st.dataframe(df_gened[cols], use_container_width=True)

    # === 回饋 & 開發者資訊（固定顯示） ===
    st.markdown("---")
    st.markdown(
        "[感謝您的使用，如果有任何建議或錯誤回報，請點此回饋表單](https://your-feedback-form-url)"
    )
    st.markdown(
        "開發者："
        "[Chu 的個人頁面](https://your-personal-homepage)"
    )

if __name__ == "__main__":
    main()
