# app.py
import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")

    # 標題與使用說明
    st.title("📄 成績單學分計算工具")
    with open("usage_guide.pdf", "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="📖 使用說明 (PDF)",
        data=pdf_bytes,
        file_name="使用說明.pdf",
        mime="application/pdf"
    )
    st.markdown("---")

    # 上傳成績單
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇成績單檔案（PDF / DOCX）",
        type=["pdf", "docx"]
    )

    # 上傳通識課程 CSV（可選）
    st.write("（選用）若已下載「通過課程 CSV」，可在此上傳以進行通識課程統計。")
    csv_file = st.file_uploader(
        "上傳通過課程 CSV",
        type=["csv"],
        key="gened_csv"
    )

    # 畫面互動邏輯
    if not uploaded_file and not csv_file:
        st.info("請先上傳成績單或「通過課程 CSV」。")
        return

    # 若使用者有上傳 CSV，直接讀取 CSV
    df_gened: pd.DataFrame = None
    if csv_file:
        try:
            df_gened = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"CSV 讀取失敗：{e}")
            df_gened = None

    # 若尚未提供 CSV，且有成績單，則解析成績單
    if df_gened is None and uploaded_file:
        filename = uploaded_file.name.lower()
        if filename.endswith(".pdf"):
            dfs = process_pdf_file(uploaded_file)
        else:
            dfs = process_docx_file(uploaded_file)

        total_credits, passed, failed = calculate_total_credits(dfs)

        st.markdown("---")
        st.markdown("## ✅ 查詢結果")
        st.markdown(
            f"<p style='font-size:32px; margin:4px 0;'>目前總學分："
            f"<strong>{total_credits:.2f}</strong></p>",
            unsafe_allow_html=True
        )
        target = st.number_input("目標學分（例如：128）", min_value=0.0, value=128.0, step=1.0)
        diff = target - total_credits
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

        # 把通過的課程列表輸出為 CSV 供使用者下載或後續再上傳
        if passed:
            df_passed = pd.DataFrame(passed)
            csv_pass = df_passed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="下載通過課程 CSV",
                data=csv_pass,
                file_name="通過課程列表.csv",
                mime="text/csv"
            )
        else:
            st.info("未偵測到任何通過的課程。")

        # 顯示不及格課程
        if failed:
            df_failed = pd.DataFrame(failed)
            st.dataframe(df_failed, use_container_width=True)
            csv_fail = df_failed.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="下載不及格課程 CSV",
                data=csv_fail,
                file_name="不及格課程列表.csv",
                mime="text/csv"
            )

    # 若已有 CSV（df_gened），則進行通識課程篩選
    if df_gened is not None:
        st.markdown("---")
        st.markdown("### 🎓 通識課程統計（CSV 來源）")
        # 檢查必要欄位
        required = ["學年度", "學期", "科目名稱", "學分"]
        if not all(col in df_gened.columns for col in required):
            st.error(f"CSV 欄位不足，需包含：{required}")
        else:
            # 篩出「人文：」「自然：」「社會：」開頭的科目
            prefixes = ("人文：", "自然：", "社會：")
            mask = df_gened["科目名稱"].astype(str).str.startswith(prefixes)
            df_gened_sel = df_gened.loc[mask, required + ["科目名稱"]].copy()
            if df_gened_sel.empty:
                st.info("CSV 中未偵測到任何通識課程。")
            else:
                # 擷取領域
                df_gened_sel["領域"] = (
                    df_gened_sel["科目名稱"]
                    .str.extract(r'^(人文：|自然：|社會：)')[0]
                    .str[:-1]
                )
                # 顯示
                st.dataframe(
                    df_gened_sel[["領域"] + required],
                    use_container_width=True
                )
                # 可選下載
                csv_out = df_gened_sel.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="下載篩選後通識課程 CSV",
                    data=csv_out,
                    file_name="通識課程篩選.csv",
                    mime="text/csv"
                )

    # 最下方：回饋 & 開發者資訊
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
