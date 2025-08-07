import pandas as pd
import re

def normalize_text(x):
    return "" if x is None else re.sub(r"\s+", " ", str(x)).strip()

def is_passing_gpa(gpa_str):
    s = normalize_text(gpa_str).upper()
    if not s: return False
    if s in ["PASS", "通過", "抵免"]: return True
    if re.match(r"^[A-C][+\-]?$", s): return True
    if s in ["D","D-","E","F","X"]: return False
    return False

def parse_credit_and_gpa(txt):
    s = normalize_text(txt)
    # e.g. "2 A+" / "A+ 2"
    m1 = re.match(r"([A-Fa-f][+\-]?)\s*(\d+(\.\d+)?)", s)
    if m1:
        return float(m1.group(2)), m1.group(1).upper()
    m2 = re.match(r"(\d+(\.\d+)?)\s*([A-Fa-f][+\-]?)", s)
    if m2:
        return float(m2.group(1)), m2.group(3).upper()
    # 單純學分
    m3 = re.match(r"(\d+(\.\d+)?)", s)
    if m3:
        return float(m3.group(1)), ""
    # 單純 GPA
    m4 = re.match(r"([A-Fa-f][+\-]?)", s)
    if m4:
        return 0.0, m4.group(1).upper()
    return 0.0, ""

def calculate_total_credits(df_list):
    total = 0.0
    passed = []
    failed = []
    for idx, df in enumerate(df_list, start=1):
        if df.shape[1] < 2:
            continue
        # 嘗試定位關鍵欄位
        cols = [c for c in df.columns]
        # 簡單匹配
        subj_col = next((c for c in cols if "科目" in c or "課程" in c), None)
        cred_col = next((c for c in cols if "學分" in c or "Credit" in c), None)
        gpa_col  = next((c for c in cols if "GPA" in c or "成績" in c), None)
        if not (subj_col and cred_col):
            continue

        for _, row in df.iterrows():
            subj = normalize_text(row.get(subj_col, ""))
            cr_txt = normalize_text(row.get(cred_col, ""))
            gp_txt = normalize_text(row.get(gpa_col, "")) if gpa_col else ""
            cr, gp = parse_credit_and_gpa(cr_txt), parse_credit_and_gpa(gp_txt)[1]
            credit, _gpa = cr[0], gp or cr[1]
            if _gpa and not is_passing_gpa(_gpa):
                failed.append({"科目名稱":subj, "學分":credit, "GPA":_gpa})
            else:
                total += credit
                passed.append({"科目名稱":subj, "學分":credit, "GPA":_gpa})
    return total, passed, failed