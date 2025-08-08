# utils/pdf_processing.py
import streamlit as st
import pandas as pd
import pdfplumber
import re
from .grade_analysis import normalize_text

def make_unique_columns(cols):
    """
    将表头去重，生成唯一列名
    """
    names = []
    seen = {}
    for c in cols:
        base = normalize_text(c) or "Column"
        cnt = seen.get(base, 0)
        name = base if cnt == 0 else f"{base}_{cnt}"
        seen[base] = cnt + 1
        names.append(name)
    return names

def is_grades_table(df):
    """
    简单判断是否成绩表格——只要同时存在“科目”“学分”两列即可
    """
    cols = [c.replace(" ", "") for c in df.columns]
    return any("科目" in c or "课程" in c for c in cols) and any("学分" in c or "Credit" in c for c in cols)

def regex_fallback_to_df(pdf):
    """
    纯文字 PDF 回退：用正则把每行拆成 (学年)(学期)(科目名)(学分)(GPA)。
    例如行格式：
      112 上 台日交流实践--农食育中的语言实践 3 A-
    """
    records = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        for line in text.split("\n"):
            # 四个捕获组：year, sem, subj, credit, gpa
            m = re.match(
                r"^\s*(\d{3,4})\s+(上|下)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+([A-F][+\-]?|通過|抵免)\s*$",
                line
            )
            if m:
                year, sem, subj, cred, gpa = m.groups()
                records.append({
                    "學年度": year,
                    "學期": sem,
                    "科目名稱": subj.strip(),
                    "學分": cred,
                    "GPA": gpa
                })
    if records:
        return pd.DataFrame(records)
    return None

def process_pdf_file(uploaded_file):
    """
    1) 尝试用 pdfplumber 抽表格；
    2) 如果一张都没抽到，则再跑 regex 回退；
    3) 返回 DataFrame 列表，供上层 calculate_total_credits 使用。
    """
    tables = []
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                extracted = page.extract_tables({
                    "vertical_strategy":"lines",
                    "horizontal_strategy":"lines",
                    "snap_tolerance":3,
                })
                for tbl in extracted or []:
                    # 规范化表格行、去掉空行
                    rows = [[normalize_text(cell) for cell in row] for row in tbl]
                    rows = [r for r in rows if any(cell for cell in r)]
                    if len(rows) < 2:
                        continue
                    df = pd.DataFrame(rows[1:], columns=make_unique_columns(rows[0]))
                    if is_grades_table(df):
                        tables.append(df)
            # 如果有表格就返回，否则尝试 regex 回退
            if tables:
                return tables

            st.info("未檢測到表格，啟用純文字回退解析…")
            fallback_df = regex_fallback_to_df(pdf)
            if fallback_df is not None:
                return [fallback_df]
            else:
                st.warning("純文字回退也未識別到任何紀錄。")
                return []
    except Exception as e:
        st.error(f"PDF 解析失敗：{e}")
        return []
