import io
import pandas as pd
from docx import Document
import streamlit as st

def process_docx_file(uploaded_file):
    """從 .docx 逐一提取表格，回傳 DataFrame list。"""
    try:
        doc = Document(io.BytesIO(uploaded_file.read()))
    except Exception as e:
        st.error(f"Word 解析失敗：{e}")
        return []

    dfs = []
    for table in doc.tables:
        rows = []
        for row in table.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        if len(rows) < 2:
            continue
        df = pd.DataFrame(rows[1:], columns=rows[0])
        dfs.append(df)
    return dfs