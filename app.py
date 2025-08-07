import streamlit as st
import pandas as pd
from utils.pdf_processing import process_pdf_file
from utils.docx_processing import process_docx_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    uploaded_file = st.file_uploader(
        "請上傳成績單檔案（支援 PDF、DOCX）", 
        type=["pdf", "docx"]
    )

    if not uploaded_file:
        st.info("請先上傳檔案，以開始學分計算。")
        return

    # 根據副檔名選擇處理函式
    if uploaded_file.name.lower().endswith(".pdf"):
        dfs = process_pdf_file(uploaded_file)
    else:
        dfs = process_docx_file(uploaded_file)

    if not dfs:
        st.error("未從檔案中提取到任何表格。請檢查檔案格式。")
        return

    total_credits, passed, failed = calculate_total_credits(dfs)

    st.markdown("---")
    # 查詢結果
    st.markdown("## ✅ 查詢結果")
    st.markdown(f"<span style='font-size:32px;'>目前總學分：**{total_credits:.2f}**</span>", unsafe_allow_html=True)

    target = st.number_input("目標學分 (例如 128)", min_value=0.0, value=128.0, step=1.0)
    diff = target - total_credits
    diff_str = f"{abs(diff):.2f}"
    if diff > 0:
        st.markdown(f"還需 <span style='color:red; font-size:24px;'>{diff_str}</span> 學分", unsafe_allow_html=True)
    else:
        st.markdown(f"已超越畢業學分：<span style='color:green; font-size:24px;'>{diff_str}</span> 學分", unsafe_allow_html=True)

    st.markdown("---")
    # 通過課程列表
    st.subheader("📚 通過的課程列表")
    if passed:
        df_pass = pd.DataFrame(passed)
        display_cols = ["學年度","學期","科目名稱","學分","GPA"]
        available = [c for c in display_cols if c in df_pass.columns]
        if available:
            st.dataframe(df_pass[available], use_container_width=True)
            csv_data = df_pass[available].to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載通過科目 CSV", data=csv_data, file_name="passed_courses.csv", mime="text/csv")
        else:
            st.info("通過課程資料中沒有可顯示的欄位。")
    else:
        st.info("沒有找到任何通過的課程。")

    st.markdown("---")
    # 不及格課程列表
    st.subheader("⚠️ 不及格的課程列表")
    if failed:
        df_fail = pd.DataFrame(failed)
        display_cols = ["學年度","學期","科目名稱","學分","GPA"]
        available = [c for c in display_cols if c in df_fail.columns]
        if available:
            st.dataframe(df_fail[available], use_container_width=True)
            csv_data = df_fail[available].to_csv(index=False, encoding="utf-8-sig")
            st.download_button("下載不及格科目 CSV", data=csv_data, file_name="failed_courses.csv", mime="text/csv")
        else:
            st.info("不及格課程資料中沒有可顯示的欄位。")
        st.caption("這些科目因成績不及格 (D、E、F 等) 未計入總學分。")
    else:
        st.info("沒有找到任何不及格的課程。")

    # ————————————————
    # 通識課程統計
    if passed:
        st.markdown("---")
        st.subheader("🎓 通識課程統計")

        df_ge = pd.DataFrame(passed)
        if "科目名稱" in df_ge.columns and "學分" in df_ge.columns:
            # 定義領域前綴與顯示名稱
            prefixes = {
                "人文：": "人文",
                "自然：": "自然",
                "社會：": "社會"
            }
            domain_sums = {}
            details = []

            # 計算各領域學分，並收集課程
            for pre, name in prefixes.items():
                mask = df_ge["科目名稱"].str.startswith(pre)
                df_dom = df_ge[mask]
                credit_sum = df_dom["學分"].astype(float).sum()
                domain_sums[name] = credit_sum
                for _, row in df_dom.iterrows():
                    details.append({
                        "領域": name,
                        "學年度": row.get("學年度",""),
                        "學期": row.get("學期",""),
                        "科目名稱": row["科目名稱"],
                        "學分": row["學分"]
                    })

            total_ge = sum(domain_sums.values())
            # 顯示統計
            st.markdown(f"- 總計通識學分：**{total_ge:.2f}**")
            for name, s in domain_sums.items():
                st.markdown(f"  - {name}：{s:.2f} 學分")
            # 顯示細節表
            if details:
                df_det = pd.DataFrame(details)
                st.dataframe(df_det[["領域","學年度","學期","科目名稱","學分"]], use_container_width=True)
            else:
                st.info("沒有符合條件的通識課程。")

    # ————————————————
    # 回饋 & 開發者資訊（置底）
    st.markdown("---")
    st.markdown(
        "[💬 感謝您的使用，若您有修改建議或其他錯誤回報，請點此填寫回饋表單]"
        "(https://your-feedback-form-url.example.com)"
    )
    st.markdown(
        "開發者："
        "[Chu](https://your-profile-url.example.com)"
    )

if __name__ == "__main__":
    main()
