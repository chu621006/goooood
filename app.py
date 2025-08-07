import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="PDF/Word 成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 使用說明
    st.markdown("[📖 使用說明 (PDF)](usage_guide.pdf)")

    st.write("請上傳 PDF (純表格) 或 Word (.docx) 格式的成績單檔案。")
    st.write("選擇一個成績單檔案（支援 PDF, DOCX）")

    uploaded_file = st.file_uploader("Drag and drop file here", type=["pdf", "docx"])
    if uploaded_file is None:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    filename = uploaded_file.name.lower()
    extracted_dfs = []
    if filename.endswith(".pdf"):
        extracted_dfs = process_pdf_file(uploaded_file)
    elif filename.endswith(".docx"):
        extracted_dfs = process_docx_file(uploaded_file)

    if not extracted_dfs:
        st.warning("未從檔案中提取到任何表格數據。請確認檔案格式或內容。")
        return

    total_credits, calculated_courses, failed_courses = calculate_total_credits(extracted_dfs)

    # 顯示總學分
    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(f"目前總學分: <span style='font-size:28px;'><b>{total_credits:.2f}</b></span>", unsafe_allow_html=True)

    # 目標學分與還差
    target_credits = st.number_input("目標學分 (例如：128)", min_value=0.0, value=128.0, step=1.0)
    diff = target_credits - total_credits
    if diff > 0:
        st.markdown(f"還需 <span style='font-size:24px; color:red;'>{diff:.2f}</span> 學分", unsafe_allow_html=True)
    elif diff < 0:
        st.markdown(f"已超出目標 <span style='font-size:24px; color:green;'>{abs(diff):.2f}</span> 學分", unsafe_allow_html=True)
    else:
        st.markdown("已精確達到目標學分！")

    # 下載通過/不及格 CSV
    st.markdown("---")
    if calculated_courses:
        df_pass = pd.DataFrame(calculated_courses)
        csv_pass = df_pass.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載通過課程 CSV", csv_pass, "passed_courses.csv", mime="text/csv")
    if failed_courses:
        df_fail = pd.DataFrame(failed_courses)
        csv_fail = df_fail.to_csv(index=False, encoding="utf-8-sig")
        st.download_button("下載不及格課程 CSV", csv_fail, "failed_courses.csv", mime="text/csv")

    # 不及格清單
    if failed_courses:
        st.markdown("### ⚠️ 不及格的課程列表")
        st.dataframe(df_fail[["科目名稱","學分","GPA"]], use_container_width=True)

    # ―――――――――――――――――
    # 新增：通識課程 CSV 上傳 (選用)
    st.markdown("---")
    st.markdown("### 🎓 通識課程篩選 (選用 CSV)")
    gen_ed_csv = st.file_uploader(
        "(選用) 若已下載「通過課程 CSV」，可直接上傳以做通識課統計。",
        type=["csv"],
        key="gened"
    )
    if gen_ed_csv:
        try:
            df_gen = pd.read_csv(gen_ed_csv, encoding="utf-8-sig")
            required = ["科目名稱", "學分"]
            missing = [c for c in required if c not in df_gen.columns]
            if missing:
                st.error(f"CSV 欄位不齊全，必須包含：{required}")
            else:
                prefixes = ("人文：", "自然：", "社會：")
                mask = df_gen["科目名稱"].astype(str).str.startswith(prefixes)
                df_sel = df_gen[mask].reset_index(drop=True)
                if df_sel.empty:
                    st.info("未偵測到任何符合通識前綴的課程。")
                else:
                    df_sel["領域"] = (
                        df_sel["科目名稱"]
                        .str.extract(r"^(人文：|自然：|社會：)")[0]
                        .str[:-1]
                    )
                    st.dataframe(df_sel[["領域","科目名稱","學分"]], use_container_width=True)
        except Exception as e:
            st.error(f"讀取 CSV 發生錯誤：{e}")

    # 回饋 & 開發者資訊（固定顯示）
    st.markdown("---")
    st.markdown(
        "[🎯 感謝您的使用，若您有修改建議或錯誤回報，請點此填寫回饋表單](https://forms.gle/your-feedback-link)"
    )
    st.markdown(
        "開發者："
        "[Chu](https://www.your-profile-link.com)  –  "
        "`Version 1.0.0`"
    )

if __name__ == "__main__":
    main()
