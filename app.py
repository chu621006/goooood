import streamlit as st
import pandas as pd
import re
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")
    st.markdown("[📖 使用說明 (PDF)](usage_guide.pdf)")

    st.write("請上傳 PDF（純表格）或 Word (.docx) 格式的成績單檔案。")
    uploaded_file = st.file_uploader(
        "選擇一個成績單檔案（支援 PDF, DOCX）",
        type=["pdf", "docx"]
    )

    if uploaded_file is None:
        st.info("請先上傳檔案，以開始學分計算。")
        st.markdown("---")
        st.write("感謝您的使用，若您有相關修改建議或發生其他類型錯誤，請點選[回饋表單](YOUR_FORM_URL)")
        st.write("開發者：[@YourName](https://example.com)")
        return

    # 根據副檔名呼叫對應處理
    if uploaded_file.name.lower().endswith(".pdf"):
        tables = process_pdf_file(uploaded_file)
    else:
        tables = process_docx_file(uploaded_file)

    total_credits, passed, failed = calculate_total_credits(tables)

    st.success("✅ 查詢結果")
    st.markdown(f"**目前總學分：** <span style='font-size:1.5em'>{total_credits:.2f}</span>", unsafe_allow_html=True)
    target = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target - total_credits
    if diff > 0:
        st.markdown(f"還需 <span style='color:red; font-size:1.2em'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
    else:
        st.write(f"已超過目標學分：{abs(diff):.2f}")

    # 已通過的課程
    if passed:
        df_pass = pd.DataFrame(passed)
        display_cols = ["學年度","學期","科目名稱","學分","GPA"]
        cols = [c for c in display_cols if c in df_pass.columns]
        st.markdown("---")
        st.markdown("📚 通過的課程列表")
        st.dataframe(df_pass[cols], use_container_width=True)
    else:
        st.info("沒有找到任何通過的課程。")

    # 不及格的課程
    if failed:
        df_fail = pd.DataFrame(failed)
        display_cols = ["學年度","學期","科目名稱","學分","GPA"]
        cols = [c for c in display_cols if c in df_fail.columns]
        st.markdown("---")
        st.markdown("⚠️ 不及格的課程列表")
        st.dataframe(df_fail[cols], use_container_width=True)
    else:
        st.info("這些科目因成績不及格 ('D','E','F' 等) 未計入總學分。")

    # ====== 通識課程統計 ======
    if passed:
        st.markdown("---")
        st.subheader("🎓 通識課程統計")

        df_ge = pd.DataFrame(passed)
        if {"科目名稱","學分"}.issubset(df_ge.columns):
            # 前綴映射
            prefixes = {"人文：":"人文","自然：":"自然","社會：":"社會"}
            # 建 regex：只要包含這些前綴就算
            pattern = re.compile("|".join(re.escape(p) for p in prefixes.keys()))

            domain_sums = {}
            details = []

            # 先篩出所有包含任一通識前綴的課程
            mask_all = df_ge["科目名稱"].astype(str).str.contains(pattern)
            df_all_ge = df_ge[mask_all]

            for pre, name in prefixes.items():
                # 本領域：科目名稱中含 pre
                mask_dom = df_all_ge["科目名稱"].str.contains(re.escape(pre))
                df_dom = df_all_ge[mask_dom]
                # 累加學分
                credit_sum = df_dom["學分"].astype(float).sum() if not df_dom.empty else 0.0
                domain_sums[name] = credit_sum

                # 存檔細節
                for _, row in df_dom.iterrows():
                    details.append({
                        "領域": name,
                        "學年度": row.get("學年度",""),
                        "學期": row.get("學期",""),
                        "科目名稱": row["科目名稱"],
                        "學分": row["學分"]
                    })

            total_ge = sum(domain_sums.values())
            st.markdown(f"- 總計通識學分：**{total_ge:.2f}**")
            for nd, cs in domain_sums.items():
                st.markdown(f"  - {nd}：{cs:.2f} 學分")

            if details:
                df_det = pd.DataFrame(details)
                st.dataframe(df_det[["領域","學年度","學期","科目名稱","學分"]],
                             use_container_width=True)
            else:
                st.info("沒有符合條件的通識課程。")

    # 回饋 & 開發者資訊
    st.markdown("---")
    st.write("感謝您的使用，若您有相關修改建議或發生其他類型錯誤，請點選[回饋表單](YOUR_FORM_URL)")
    st.write("開發者：[@YourName](https://example.com)")

if __name__ == "__main__":
    main()
