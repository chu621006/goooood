# app.py
import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits


def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")

    # 標題
    st.title("📄 成績單學分計算工具")

    # 使用說明下載按鈕
    with open("usage_guide.pdf", "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="📖 使用說明 (PDF)",
        data=pdf_bytes,
        file_name="使用說明.pdf",
        mime="application/pdf"
    )

    # 錯誤修正下載按鈕
    with open("notfound_fix.pdf", "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="⚠️「未識別到任何紀錄」處理方式(PDF)",
        data=pdf_bytes,
        file_name="「未識別到任何紀錄」處理.pdf",
        mime="application/pdf"
    )

    # 上傳成績單區
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF、DOCX）",
        type=["pdf", "docx"]
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
    else:
        # 根據副檔名選擇處理函式
        name_lower = uploaded_file.name.lower()
        if name_lower.endswith(".pdf"):
            dfs = process_pdf_file(uploaded_file)
        else:
            dfs = process_docx_file(uploaded_file)

        total_credits, passed, failed = calculate_total_credits(dfs)

        # 分隔線
        st.markdown("---")
        # 查詢結果
        st.markdown("## ✅ 查詢結果")
        # 總學分顯示
        st.markdown(
            f"<p style='font-size:32px; margin:4px 0;'>目前總學分：<strong>{total_credits:.2f}</strong></p>",
            unsafe_allow_html=True
        )
        # 目標與差額
        target = st.number_input("目標學分（例如：128）", min_value=0.0, value=128.0, step=1.0)
        diff = target - total_credits
        if diff > 0:
            st.markdown(
                f"<p style='font-size:24px;'>還需 <span style='color:red;'>{diff:.2f}</span> 學分</p>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<p style='font-size:24px;'>已超出畢業學分 <span style='color:red;'>{abs(diff):.2f}</span> 學分</p>",
                unsafe_allow_html=True
            )

        # 通過課程列表
        st.markdown("### 📚 通過的課程列表")
        if passed:
            df_passed = pd.DataFrame(passed)
            st.dataframe(df_passed, use_container_width=True)
            csv_pass = df_passed.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="下載通過課程 CSV",
                data=csv_pass,
                file_name="通過課程列表.csv",
                mime="text/csv"
            )
        else:
            st.info("未偵測到任何通過的課程。")

        # 不及格課程列表
        st.markdown("### ⚠️ 不及格的課程列表")
        if failed:
            df_failed = pd.DataFrame(failed)
            st.dataframe(df_failed, use_container_width=True)
            csv_fail = df_failed.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="下載不及格課程 CSV",
                data=csv_fail,
                file_name="不及格課程列表.csv",
                mime="text/csv"
            )
        else:
            st.info("未偵測到任何不及格的課程。")

        # --- 新增：通識學分計算(僅供電腦用戶使用) ---
    st.markdown("---")
    st.markdown("## 🎓 通識學分計算(僅供電腦用戶使用)")
    gen_docx = st.file_uploader(
        "請上傳 Word 檔(.docx) 以計算通識學分（單獨功能）", type=["docx"], key="gened_word"
    )
    if gen_docx:
        dfs_gen = process_docx_file(gen_docx)
        _, passed_gen, _ = calculate_total_credits(dfs_gen)
        df_gen = pd.DataFrame(passed_gen)
        if df_gen.empty:
            st.info("未偵測到任何課程資料。請確認上傳的 Word 檔案格式正確。")
        else:
            # 篩選通識前綴
            prefixes = ("人文：", "自然：", "社會：")
            mask = df_gen["科目名稱"].astype(str).str.startswith(prefixes)
            df_selected = df_gen[mask].reset_index(drop=True)
            if df_selected.empty:
                st.info("未偵測到任何符合通識前綴的課程。")
            else:
                # 計算總學分
                total_gen = df_selected["學分"].sum()
                st.markdown(f"**通識總學分：{total_gen:.0f}**")
                # 計算各領域學分
                domain_sums = df_selected.groupby(df_selected["科目名稱"].str.extract(r"^(人文：|自然：|社會：)")[0].str[:-1])["學分"].sum()
                st.markdown("**各領域學分：**")
                for domain, credits in domain_sums.items():
                    st.write(f"- {domain}：{credits:.0f} 學分")
                # 提取領域欄
                df_selected["領域"] = (
                    df_selected["科目名稱"]
                    .str.extract(r"^(人文：|自然：|社會：)")[0]
                    .str[:-1]
                )
                st.dataframe(
                    df_selected[["領域", "科目名稱", "學分"]], use_container_width=True
               
    st.markdown("---")
    st.markdown("## 🎓 通識學分計算(僅供電腦用戶使用)")
    gen_docx = st.file_uploader(
        "請上傳 Word 檔(.docx) 以計算通識學分（單獨功能）", type=["docx"], key="gened_word"
    )
    if gen_docx:
        dfs_gen = process_docx_file(gen_docx)
        _, passed_gen, _ = calculate_total_credits(dfs_gen)
        df_gen = pd.DataFrame(passed_gen)
        if df_gen.empty:
            st.info("未偵測到任何通識課程。")
        else:
            # 篩選通識前綴
            prefixes = ("人文：", "自然：", "社會：")
            mask = df_gen["科目名稱"].astype(str).str.startswith(prefixes)
            df_selected = df_gen[mask].reset_index(drop=True)
            if df_selected.empty:
                st.info("未偵測到任何符合通識前綴的課程。")
            else:
                # 計算總學分
                total_gen = df_selected["學分"].sum()
                st.markdown(f"**通識總學分：{total_gen:.0f}**")
                # 提取領域
                df_selected["領域"] = (
                    df_selected["科目名稱"].str.extract(r"^(人文：|自然：|社會：)")[0].str[:-1]
                )
                st.dataframe(
                    df_selected[["領域", "科目名稱", "學分"]], use_container_width=True
                )

if __name__ == "__main__":
    main()

