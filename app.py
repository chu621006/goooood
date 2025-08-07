import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")

    # --- 標題 & 使用說明、錯誤修正按鈕 ---
    st.title("📄 成績單學分計算工具")

    with open("usage_guide.pdf", "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="📖 使用說明 (PDF)",
        data=pdf_bytes,
        file_name="使用說明.pdf",
        mime="application/pdf"
    )

    with open("notfound_fix.pdf", "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="⚠️「未識別到任何紀錄」處理方式(PDF)",
        data=pdf_bytes,
        file_name="「未識別到任何紀錄」處理.pdf",
        mime="application/pdf"
    )

    # --- 檔案上傳 & 學分計算流程 ---
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF、DOCX）",
        type=["pdf", "docx"]
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 依副檔名處理
    fn = uploaded_file.name.lower()
    if fn.endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    else:
        dfs = process_docx_file(uploaded_file)

    total_credits, passed, failed = calculate_total_credits(dfs)

    # --- 顯示查詢結果 ---
    st.markdown("---")
    st.markdown("## ✅ 查詢結果")

    # 目前總學分（大字）
    st.markdown(
        f"<p style='font-size:32px; margin:4px 0;'>目前總學分："
        f"<strong>{total_credits:.2f}</strong></p>",
        unsafe_allow_html=True
    )

    # 目標 & 還需學分（紅字）
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

    # 通過的課程列表
    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_passed = pd.DataFrame(passed)
        st.dataframe(df_passed, use_container_width=True)
        csv_passed = df_passed.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下載通過課程 CSV",
            data=csv_passed,
            file_name="通過課程列表.csv",
            mime="text/csv"
        )
    else:
        st.info("未偵測到任何通過的課程。")

    # 不及格的課程列表
    st.markdown("### ⚠️ 不及格的課程列表")
    if failed:
        df_failed = pd.DataFrame(failed)
        st.dataframe(df_failed, use_container_width=True)
        csv_failed = df_failed.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下載不及格課程 CSV",
            data=csv_failed,
            file_name="不及格課程列表.csv",
            mime="text/csv"
        )
    else:
        st.info("未偵測到任何不及格的課程。")

    # --- 新增：通識課程 CSV / DOCX 上傳 (選用) ---
st.markdown("---")
st.markdown("### 🎓 通識課程篩選 (選用 CSV / DOCX)")
gened_file = st.file_uploader(
    "(選用) 上傳「通過課程 CSV」或原始 Word (DOCX) 來進行通識課統計。",
    type=["csv", "docx"],
    key="gened"
)
if gened_file:
    try:
        # 1) CSV 直接讀
        if gened_file.name.lower().endswith(".csv"):
            df_gen = pd.read_csv(gened_file, encoding="utf-8-sig")
        # 2) DOCX 重新解析 passed list
        else:
            # 利用你原本的 docx 處理流程拿到 passed 資料
            dfs2 = process_docx_file(gened_file)
            _, passed2, _ = calculate_total_credits(dfs2)
            df_gen = pd.DataFrame(passed2)

        # 欄位檢查
        required = ["科目名稱", "學分"]
        missing = [c for c in required if c not in df_gen.columns]
        if missing:
            st.error(f"上傳檔案不包含必要欄位：{required}")
        else:
            # 統一把全形「：」換成半形「:」，並去掉左右空白
            df_gen["科目名稱"] = (
                df_gen["科目名稱"]
                .astype(str)
                .str.replace("：", ":", regex=False)
                .str.strip()
            )
            # 前綴篩選
            prefixes = ("人文:", "自然:", "社會:")
            mask = df_gen["科目名稱"].str.startswith(prefixes)
            df_sel = df_gen[mask].reset_index(drop=True)

            if df_sel.empty:
                st.info("未偵測到任何符合通識前綴的課程。")
            else:
                # 抽出「領域」
                df_sel["領域"] = (
                    df_sel["科目名稱"]
                    .str.extract(r"^(人文:|自然:|社會:)")[0]
                    .str[:-1]
                )
                st.dataframe(df_sel[["領域", "科目名稱", "學分"]], use_container_width=True)
    except Exception as e:
        st.error(f"通識課程篩選時發生錯誤：{e}")

    # --- 回饋 & 開發者資訊（固定顯示） ---
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;">'
        '感謝您的使用，若您有相關修改建議或發生其他類型錯誤，'
        '<a href="https://forms.gle/Bu95Pt74d1oGVCev5" target="_blank">請點此提出</a>'
        '</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center;">'
        '開發者：<a href="https://www.instagram.com/chiuuuuu11.7?igsh=MWRlc21zYW55dWZ5Yw==" target="_blank">Chu</a>'
        '</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()


