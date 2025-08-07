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
    
    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF、DOCX）",
        type=["pdf", "docx"]
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
    else:
        # 根據副檔名選擇對應的處理函式
        filename = uploaded_file.name.lower()
        if filename.endswith(".pdf"):
            dfs = process_pdf_file(uploaded_file)
        else:
            dfs = process_docx_file(uploaded_file)

        total_credits, passed, failed = calculate_total_credits(dfs)

        st.markdown("---")
        # 查詢結果
        st.markdown("## ✅ 查詢結果")
        # 總學分（字體放大）
        st.markdown(
            f"<p style='font-size:32px; margin:4px 0;'>目前總學分："
            f"<strong>{total_credits:.2f}</strong></p>",
            unsafe_allow_html=True
        )

        # 還需學分（數字紅色顯示）
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

        # —— 新增：通識課程統計 —— #
        st.markdown("### 🎓 通識課程統計")
        if passed:
            # 只要「科目名稱」存在，就篩選前綴
            if "科目名稱" in df_passed.columns:
                prefixes = ("人文：", "自然：", "社會：")
                gen_ed_mask = df_passed["科目名稱"].str.startswith(prefixes, na=False)
                df_gen_ed = df_passed[gen_ed_mask]
            else:
                df_gen_ed = pd.DataFrame()  # 沒有「科目名稱」欄位，直接空

            if not df_gen_ed.empty:
                # 只取實際存在的欄位
                wanted = ["學年度", "學期", "科目名稱", "學分"]
                cols = [c for c in wanted if c in df_gen_ed.columns]
                st.dataframe(df_gen_ed[cols], use_container_width=True)
            else:
                st.info("未偵測到任何通識課程。")
        else:
            st.info("未偵測到任何通識課程。")
            
    # 底部分隔線
    st.markdown("---")
    # 回饋連結
    st.markdown(
        '<p style="text-align:center;">'
        '感謝您的使用，若您有相關修改建議或發生其他類型錯誤，'
        '<a href="https://forms.gle/Bu95Pt74d1oGVCev5" target="_blank">請點此提出</a>'
        '</p>',
        unsafe_allow_html=True
    )
    # 開發者資訊
    st.markdown(
        '<p style="text-align:center;">'
        '開發者：<a href="https://www.instagram.com/chiuuuuu11.7?igsh=MWRlc21zYW55dWZ5Yw==" target="_blank">Chu</a>'
        '</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()

