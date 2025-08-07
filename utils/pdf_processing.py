import streamlit as st
import pandas as pd
import pdfplumber
import collections
import re

from .grade_analysis import parse_credit_and_gpa, is_passing_gpa  # if needed


def normalize_text(cell_content):
    """
    標準化從 pdfplumber 提取的單元格內容。
    處理 None 值、pdfplumber 的 Text 物件和普通字串。
    將多個空白字元（包括換行）替換為單個空格，並去除兩端空白。
    """
    if cell_content is None:
        return ""

    text = ""
    if hasattr(cell_content, 'text'):
        text = str(cell_content.text)
    elif isinstance(cell_content, str):
        text = cell_content
    else:
        text = str(cell_content)

    return re.sub(r'\s+', ' ', text).strip()


def make_unique_columns(columns_list):
    """
    將列表中的欄位名稱轉換為唯一的名稱，處理重複和空字串。
    如果遇到重複或空字串，會添加後綴 (例如 'Column_1', '欄位_2')。
    """
    seen = collections.defaultdict(int)
    unique_columns = []
    for col in columns_list:
        original_col_cleaned = normalize_text(col)
        if not original_col_cleaned or len(original_col_cleaned) < 2:
            name_base = "Column"
            current_idx = 1
            while f"{name_base}_{current_idx}" in unique_columns:
                current_idx += 1
            name = f"{name_base}_{current_idx}"
        else:
            name = original_col_cleaned

        final_name = name
        counter = seen[name]
        while final_name in unique_columns:
            counter += 1
            final_name = f"{name}_{counter}"

        unique_columns.append(final_name)
        seen[name] = counter

    return unique_columns


def is_grades_table(df):
    """
    判斷一個 DataFrame 是否為有效的成績單表格。
    透過檢查是否存在預期的欄位關鍵字和數據內容模式來判斷。
    """
    if df.empty or len(df.columns) < 3:
        return False

    normalized_columns = [re.sub(r'\s+', '', col).lower() for col in df.columns]
    credit_keywords = ["學分", "credits", "credit", "學分數"]
    gpa_keywords = ["gpa", "成績", "grade"]
    subject_keywords = ["科目名稱", "課程名稱", "coursename"]
    year_keywords = ["學年", "year"]
    semester_keywords = ["學期", "semester"]

    has_credit = any(any(k in col for k in credit_keywords) for col in normalized_columns)
    has_gpa = any(any(k in col for k in gpa_keywords) for col in normalized_columns)
    has_subject = any(any(k in col for k in subject_keywords) for col in normalized_columns)
    has_year = any(any(k in col for k in year_keywords) for col in normalized_columns)
    has_sem = any(any(k in col for k in semester_keywords) for col in normalized_columns)

    if has_subject and (has_credit or has_gpa) and has_year and has_sem:
        return True

    # fallback: check data patterns
    sample = df.head(min(len(df), 20))
    # implement additional checks if needed
    return False


def process_pdf_file(uploaded_file):
    """
    使用 pdfplumber 處理上傳的 PDF 檔案，提取表格或純文字，返回成績表格 DataFrame 列表。
    """
    all_grades_data = []

    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 嘗試表格抽取
                table_settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "snap_tolerance": 3,
                    "join_tolerance": 5,
                    "edge_min_length": 3,
                    "text_tolerance": 2,
                    "min_words_vertical": 1,
                    "min_words_horizontal": 1,
                }
                tables = page.extract_tables(table_settings)
                page_had_table = False

                for idx, table in enumerate(tables):
                    processed = [[normalize_text(cell) for cell in row] for row in table]
                    if not processed or len(processed[0]) < 3:
                        continue

                    df_table = pd.DataFrame(processed[1:], columns=make_unique_columns(processed[0]))
                    if is_grades_table(df_table):
                        all_grades_data.append(df_table)
                        page_had_table = True
                        st.success(f"頁面 {page_num+1} 表格 {idx+1} 已識別並處理。")
                    else:
                        st.info(f"頁面 {page_num+1} 表格 {idx+1} 非成績表格，已跳過。")

                # 如果本頁沒表格，使用文字 fallback
                if not page_had_table:
                    text = page.extract_text()
                    if text:
                        lines = text.split("\n")
                        rows = []
                        # 正則匹配: 學年 學期 課程名稱 學分 GPA
                        pat = re.compile(
                            r'(?P<year>\d{3,4})\s+' +
                            r'(?P<sem>上|下|春|夏|秋|冬|1|2)\s+' +
                            r'(?P<course>.+?)\s+' +
                            r'(?P<credit>\d+(?:\.\d+)?)\s+' +
                            r'(?P<gpa>[A-F][+\-]?|通過|抵免)'
                        )
                        for line in lines:
                            m = pat.match(line.strip())
                            if m:
                                rows.append({
                                    "學年": m.group("year"),
                                    "學期": m.group("sem"),
                                    "科目名稱": m.group("course"),
                                    "學分": m.group("credit"),
                                    "GPA": m.group("gpa"),
                                })
                        if rows:
                            df_fallback = pd.DataFrame(rows)
                            all_grades_data.append(df_fallback)
                            st.info(f"頁面 {page_num+1} 文字 fallback 偵測到 {len(rows)} 筆課程。")

    except Exception as e:
        st.error(f"處理 PDF 時發生錯誤: {e}")

    return all_grades_data
