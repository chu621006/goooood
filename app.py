import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx
from utils.grade_analysis import calculate_total_credits

# --- Streamlit 應用主體 ---
def main():
    st.set_page_config(page_title="學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 原有 PDF/Word 上傳與學分計算功能... (不變)
    # ...

    # --- 新增：通識學分計算 (僅供電腦用戶使用) ---
    st.markdown("---")
    st.markdown("### 🎓 通識學分計算 (僅供電腦用戶使用)")
    gened_file = st.file_uploader(
        "請上傳 Word (.docx) 格式之通識課程清單", 
        type=["docx"],
        key="gened_word"
    )
    if gened_file:
        try:
            # 解析 .docx 檔，回傳 DataFrame，須包含「科目名稱」「學分」欄位
            df_gened = process_docx(gened_file)
            # 必要欄位檢查
            if not all(col in df_gened.columns for col in ["科目名稱", "學分"]):
                st.error("解析結果缺少「科目名稱」或「學分」欄位，無法計算通識學分。")
            else:
                # 篩選前綴
                prefixes = ("人文：", "自然：", "社會：")
                mask = df_gened["科目名稱"].astype(str).str.startswith(prefixes)
                df_sel = df_gened[mask].reset_index(drop=True)
                if df_sel.empty:
                    st.info("未偵測到任何符合通識前綴的課程。")
                else:
                    # 提取領域
                    df_sel["領域"] = (
                        df_sel["科目名稱"]
                        .str.extract(r"^(人文：|自然：|社會：)")[0]
                        .str[:-1]
                    )
                    # 計算總學分與各領域分
                    total = df_sel["學分"].sum()
                    by_domain = df_sel.groupby("領域")["學分"].sum().to_dict()
                    st.write(f"**總計通識學分：{total:.2f}**")
                    for d in ["人文", "自然", "社會"]:
                        st.write(f"- {d}：{by_domain.get(d, 0):.2f} 學分")
                    # 列出通識課程清單
                    st.dataframe(df_sel[["領域", "科目名稱", "學分"]], use_container_width=True)
        except Exception as e:
            st.error(f"解析 Word 檔案時發生錯誤：{e}")

if __name__ == "__main__":
    main()
