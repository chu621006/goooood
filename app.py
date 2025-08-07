# app.py
import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    # ----------- 基本設定 -----------
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    
    # ----------- 標題 & 使用說明 -----------
    st.title("📄 成績單學分計算工具")
    # 使用說明 PDF（同目錄下的 usage_guide.pdf）
    try:
        with open("usage_guide.pdf", "rb") as f:
            guide_bytes = f.read()
        st.download_button(
            label="📖 使用說明 (PDF)",
            data=guide_bytes,
            file_name="使用說明.pdf",
            mime="application/pdf"
        )
    except FileNotFoundError:
        st.warning("未找到使用說明檔案。")

    st.markdown("---")

    # ----------- 上傳區塊 -----------
    st.subheader("📥 上傳成績單或 CSV")
    # 成績單上傳：PDF / DOCX
    uploaded_file = st.file_uploader(
        "請上傳成績單（PDF 純表格 或 .docx）",
        type=["pdf", "docx"],
        key="grade_uploader"
    )
    # 通過課程 CSV 上傳（選用）
    csv_file = st.file_uploader(
        "（選用）上傳「通過課程 CSV」以做通識課程統計",
        type=["csv"],
        key="gened_csv_uploader"
    )

    # 若兩者都沒上傳，提示並結束
    if not uploaded_file and not csv_file:
        st.info("請上傳成績單或（選用）「通過課程 CSV」。")
        return

    # ----------- 若有 CSV，直接讀取 CSV 供後續通識篩選 -----------
    df_gened: pd.DataFrame = None
    if csv_file is not None:
        try:
            df_gened = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"CSV 讀取失敗：{e}")
            df_gened = None

    # ----------- 如果沒有 CSV、但有上傳成績單，先解析成績單 -----------
    df_passed = df_failed = None
    total_credits = None
    if df_gened is None and uploaded_file is not None:
        name = uploaded_file.name.lower()
        # 解析 PDF / DOCX
        if name.endswith(".pdf"):
            dfs = process_pdf_file(uploaded_file)
        else:
            dfs = process_docx_file(uploaded_file)
        # 計算學分
        total_credits, passed, failed = calculate_total_credits(dfs)
        df_passed = pd.DataFrame(passed)
        df_failed = pd.DataFrame(failed)

        # 顯示學分查詢結果
        st.markdown("---")
        st.subheader("✅ 查詢結果")
        # 大一點的總學分
        st.markdown(
            f"<p style='font-size:32px; margin:4px 0;'>目前總學分："
            f"<strong>{total_credits:.2f}</strong></p>",
            unsafe_allow_html=True
        )
        # 目標學分輸入
        target = st.number_input("目標學分（例如：128）", min_value=0.0, value=128.0, step=1.0)
        diff = target - total_credits
        # 提示「還需 xx 學分」，數字紅色，大一點
        if diff > 0:
            st.markdown(
                f"<p style='font-size:24px;'>還需 "
                f"<span style='color:red;'>{diff:.2f}</span> 學分</p>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<p style='font-size:24px;'>已超出畢業學分 "
                f"<span style='color:red;'>{abs(diff):.2f}</span> 學分</p>",
                unsafe_allow_html=True
            )

        # 下載通過課程 CSV
        if not df_passed.empty:
            csv_pass = df_passed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="下載通過課程 CSV",
                data=csv_pass,
                file_name="通過課程列表.csv",
                mime="text/csv"
            )
        else:
            st.info("未偵測到任何通過的課程。")

        # 顯示不及格課程 & 下載
        if not df_failed.empty:
            st.markdown("---")
            st.subheader("⚠️ 不及格的課程列表")
            st.dataframe(df_failed, use_container_width=True)
            csv_fail = df_failed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="下載不及格課程 CSV",
                data=csv_fail,
                file_name="不及格課程列表.csv",
                mime="text/csv"
            )

    # ----------- 最後：做通識課程篩選（若 df_gened or df_passed） -----------
    # 優先使用上傳的 CSV，其次使用剛解析出來的 df_passed
    df_source = df_gened if df_gened is not None else df_passed
    if df_source is not None:
        st.markdown("---")
        st.subheader("🎓 通識課程統計")
        # 檢查欄位
        needed = ["學年度", "學期", "科目名稱", "學分"]
        if not all(col in df_source.columns for col in needed):
            st.error(f"無法篩選通識：需包含欄位 {needed}")
        else:
            # 篩出科目前綴符合的通識課程
            prefixes = ("人文：", "自然：", "社會：")
            mask = df_source["科目名稱"].astype(str).str.startswith(prefixes)
            df_gened_sel = df_source.loc[mask, needed + ["科目名稱"]].copy()
            if df_gened_sel.empty:
                st.info("未偵測到任何通識課程。")
            else:
                # 擷取「領域」
                df_gened_sel["領域"] = (
                    df_gened_sel["科目名稱"]
                    .str.extract(r'^(人文：|自然：|社會：)')[0]
                    .str[:-1]
                )
                # 顯示篩選後表格
                st.dataframe(df_gened_sel[["領域"] + needed], use_container_width=True)
                # 提供下載
                out_csv = df_gened_sel.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="下載篩選後通識課程 CSV",
                    data=out_csv,
                    file_name="通識課程篩選.csv",
                    mime="text/csv"
                )

    # ----------- 回饋 & 開發者 資訊（置底固定顯示） -----------
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;">感謝您的使用，若您有相關修改建議或發生其他類型錯誤，'
        '<a href="https://forms.gle/Bu95Pt74d1oGVCev5" target="_blank">請點此提出</a></p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center;">開發者：'
        '<a href="https://www.instagram.com/chiuuuuu11.7?igsh=MWRlc21zYW55dWZ5Yw==" target="_blank">Chu</a></p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
