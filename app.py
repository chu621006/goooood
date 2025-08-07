import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

# --- 主程式 ---
def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")

    # 標題與使用說明下載
    st.title("📄 成績單學分計算工具")
    with open("usage_guide.pdf", "rb") as f:
        guide = f.read()
    st.download_button("📖 使用說明 (PDF)", guide, "使用說明.pdf", "application/pdf")
    with open("notfound_fix.pdf", "rb") as f:
        fix = f.read()
    st.download_button("⚠️「未識別到任何紀錄」處理方式(PDF)", fix, "未識別到任何紀錄處理.pdf", "application/pdf")

    st.write("請上傳 PDF（純表格）、Word (.docx) 格式的成績單檔案。")
    uploaded = st.file_uploader("選擇成績單檔案（支援 PDF / DOCX）", type=["pdf","docx"])

    if not uploaded:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 根據檔案類型解析
    name = uploaded.name.lower()
    if name.endswith('.pdf'):
        tables = process_pdf_file(uploaded)
    else:
        tables = process_docx_file(uploaded)

    total, passed, failed = calculate_total_credits(tables)

    # 查詢結果
    st.markdown("---")
    st.markdown("## ✅ 查詢結果")
    st.markdown(
        f"<p style='font-size:32px;'>目前總學分：<strong>{total:.2f}</strong></p>",
        unsafe_allow_html=True
    )
    target = st.number_input("目標學分（例如：128）", min_value=0.0, value=128.0)
    remain = target - total
    if remain > 0:
        st.markdown(
            f"<p style='font-size:24px;'>還需 <span style='color:red;'>{remain:.2f}</span> 學分</p>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<p style='font-size:24px;'>已超出畢業學分 <span style='color:red;'>{abs(remain):.2f}</span> 學分</p>",
            unsafe_allow_html=True
        )

    # 通過課程列表
    st.markdown("---")
    st.markdown("### 📚 通過的課程列表")
    if passed:
        df_pass = pd.DataFrame(passed)
        st.dataframe(df_pass, use_container_width=True)
        csv_p = df_pass.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("下載通過課程 CSV", csv_p, "通過課程列表.csv", "text/csv")
    else:
        st.info("未偵測到任何通過的課程。")

    # 不及格課程列表
    st.markdown("### ⚠️ 不及格的課程列表")
    if failed:
        df_fail = pd.DataFrame(failed)
        st.dataframe(df_fail, use_container_width=True)
        csv_f = df_fail.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("下載不及格課程 CSV", csv_f, "不及格課程列表.csv", "text/csv")
    else:
        st.info("未偵測到任何不及格的課程。")

    # --- 新增：通識課程 CSV / DOCX 上傳 (選用) ---
    st.markdown("---")
    st.markdown("### 🎓 通識課程篩選 (選用) CSV 或 Word")
    gen_file = st.file_uploader(
        "(選用) 若已下載「通過課程 CSV」或成績 Word 可直接上傳做通識篩選。", 
        type=["csv","docx"], key="gened"
    )
    if gen_file:
        try:
            if gen_file.name.lower().endswith('.csv'):
                df_gen = pd.read_csv(gen_file, encoding='utf-8-sig')
            else:
                # 解析 Word 內容為通過列表
                docs = process_docx_file(gen_file)
                _, passed_gen, _ = calculate_total_credits(docs)
                df_gen = pd.DataFrame(passed_gen)

            # 欄位檢查
            req = ["科目名稱","學分"]
            if any(col not in df_gen.columns for col in req):
                st.error(f"CSV/DOCX 欄位不足，需包含：{req}")
            else:
                prefixes = ("人文：","自然：","社會：")
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
            st.error(f"讀取通識檔案發生錯誤：{e}")

    # 底部：回饋 & 開發者資訊
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;">感謝使用，若有修改建議或其他錯誤，'
        '<a href="https://forms.gle/Bu95Pt74d1oGVCev5" target="_blank">點此提出</a></p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align:center;">開發者：'
        '<a href="https://www.instagram.com/chiuuuuu11.7?igsh=MWRlc21zYW55dWZ5Yw==" target="_blank">Chu</a></p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
