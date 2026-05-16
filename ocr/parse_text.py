import re


def _clean_number(value):
    if value is None:
        return None

    value = str(value).strip()
    value = value.replace("L", "1").replace("l", "1")
    value = value.replace(",", ".")

    match = re.search(r"[-+]?\d*\.?\d+", value)
    if not match:
        return None

    num = float(match.group())

    if num.is_integer():
        return int(num)

    return num


def _find_first(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = _clean_number(match.group(1))
            if value is not None:
                return value
    return None


def parse_cbc_report(text):
    """
    Parse extracted medical text from PDF/Image/TXT/DOCX reports.
    Supports common CBC, Thyroid, Echo, and Hearing report formats.
    """

    if not text:
        return {}

    structured_data = {}

    patterns = {
        "Age": [
            r"\bAge\s*[:\-]?\s*(\d+)",
            r"\bAge\s*[:\-]?\s*(\d+)\s*(?:years|year|yrs|yr)"
        ],

        "Hemoglobin": [
            r"\bHemoglobin\s*(?:\(Hb\))?\s*[:\-]?\s*([\d\.]+)",
            r"\bHaemoglobin\s*[:\-]?\s*([\d\.]+)",
            r"\bHB\s*[:\-]?\s*([\d\.]+)",
            r"\bHGB\s*[:\-]?\s*([\d\.]+)"
        ],

        "RBC_Count": [
            r"\bRBC\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)",
            r"\bR\.?B\.?C\.?\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)",
            r"\bTotal\s*R\.?B\.?C\.?\s*Count\s*[:\-]?\s*([\d\.]+)",
            r"\bRed\s*Blood\s*Cell\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)"
        ],

        "WBC_Count": [
            r"\bWBC\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)",
            r"\bW\.?B\.?C\.?\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)",
            r"\bTotal\s*W\.?B\.?C\.?\s*Count\s*[:\-]?\s*([\d\.]+)",
            r"\bWhite\s*Blood\s*Cell\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)"
        ],

        "MCV": [
            r"\bMCV\s*[:\-]?\s*([\d\.]+)",
            r"\bMean\s*Corpuscular\s*Volume\s*(?:\(M\.?C\.?V\.?\))?\s*[:\-]?\s*([\d\.]+)"
        ],

        "TSH": [
            r"\bTSH\s*[:\-]?\s*([\d\.]+)",
            r"\bThyroid\s*Stimulating\s*Hormone\s*[:\-]?\s*([\d\.]+)"
        ],

        "T4": [
            r"\bT4\s*[:\-]?\s*([\d\.]+)",
            r"\bThyroxine\s*[:\-]?\s*([\d\.]+)"
        ],

        "Echo_Abnormality_Score": [
            r"\bEcho\s*Abnormality\s*Score\s*[:\-]?\s*([\d\.]+)",
            r"\bEchocardiogram\s*Score\s*[:\-]?\s*([\d\.]+)",
            r"\bEcho\s*Score\s*[:\-]?\s*([\d\.]+)"
        ],

        "Hearing_Loss_dB": [
            r"\bHearing\s*Loss\s*dB\s*[:\-]?\s*([\d\.]+)",
            r"\bHearing\s*Loss\s*[:\-]?\s*([\d\.]+)",
            r"\bHearing\s*Assessment\s*[:\-]?\s*([\d\.]+)"
        ]
    }

    for feature, regex_list in patterns.items():
        value = _find_first(text, regex_list)
        if value is not None:
            structured_data[feature] = value

    # Smart corrections
    if "Hemoglobin" in structured_data and structured_data["Hemoglobin"] > 30:
        structured_data["Hemoglobin"] = structured_data["Hemoglobin"] / 10.0

    if "WBC_Count" in structured_data:
        if structured_data["WBC_Count"] < 100:
            structured_data["WBC_Count"] = int(structured_data["WBC_Count"] * 1000)

    if "RBC_Count" in structured_data and structured_data["RBC_Count"] > 20:
        structured_data["RBC_Count"] = structured_data["RBC_Count"] / 10.0

    if "MCV" in structured_data and structured_data["MCV"] > 200:
        structured_data["MCV"] = structured_data["MCV"] / 10.0

    return structured_data


if __name__ == "__main__":
    sample_text = """
    COMPLETE BLOOD COUNT

    Haemoglobin : 9.10 gm/dl
    Total R.B.C. Count : 3.19 mill/cmm
    Mean Corpuscular Volume (M.C.V.) : 85.30 fl
    Total W.B.C. Count : 10560 /ul

    TSH: 6.2
    T4: 0.9
    Echo Abnormality Score: 2
    Hearing Loss dB: 35
    """

    print(parse_cbc_report(sample_text))