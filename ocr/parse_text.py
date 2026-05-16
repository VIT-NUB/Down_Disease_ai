import re


def _clean_number(value):
    """
    Clean and convert extracted numeric values.
    Handles common OCR mistakes.
    """
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


def parse_cbc_report(text):
    """
    Parse raw extracted text from PDF/Image/TXT/DOCX medical reports.
    Extracts structured medical values required by the AI model.
    """

    structured_data = {}

    patterns = {
        "Age": [
            r"\bAge\s*[:\-]?\s*(\d+)",
            r"\bAge\s*[:\-]?\s*(\d+)\s*(?:years|year|yrs|yr)"
        ],

        "Hemoglobin": [
            r"\bHemoglobin\s*(?:\(Hb\))?\s*[:\-]?\s*([\d\.]+)",
            r"\bHB\s*[:\-]?\s*([\d\.]+)",
            r"\bHGB\s*[:\-]?\s*([\d\.]+)"
        ],

        "RBC_Count": [
            r"\bRBC\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)",
            r"\bRed Blood Cell\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)"
        ],

        "WBC_Count": [
            r"\bWBC\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)",
            r"\bWhite Blood Cell\s*(?:Count)?\s*[:\-]?\s*([\d\.]+)"
        ],

        "MCV": [
            r"\bMCV\s*[:\-]?\s*([\d\.]+)"
        ],

        "TSH": [
            r"\bTSH\s*[:\-]?\s*([\d\.]+)"
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
        for pattern in regex_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = _clean_number(match.group(1))

                if value is not None:
                    structured_data[feature] = value
                    break

    # Smart correction for common report units / OCR cases
    if "Hemoglobin" in structured_data and structured_data["Hemoglobin"] > 30:
        structured_data["Hemoglobin"] = structured_data["Hemoglobin"] / 10.0

    if "WBC_Count" in structured_data:
        # If WBC is written as 18.5 x10^3/uL, convert to 18500
        if structured_data["WBC_Count"] < 100:
            structured_data["WBC_Count"] = int(structured_data["WBC_Count"] * 1000)

    if "RBC_Count" in structured_data and structured_data["RBC_Count"] > 20:
        structured_data["RBC_Count"] = structured_data["RBC_Count"] / 10.0

    if "MCV" in structured_data and structured_data["MCV"] > 200:
        structured_data["MCV"] = structured_data["MCV"] / 10.0

    return structured_data


if __name__ == "__main__":
    sample_text = """
    Patient Name: Sherif Ahmed
    Age: 8 Years

    Hemoglobin: 9.4 g/dL
    RBC Count: 3.8 million/uL
    WBC Count: 12800 /uL
    MCV: 74 fL

    TSH: 6.2 mIU/L
    T4: 0.9 ng/dL

    Echo Abnormality Score: 2
    Hearing Loss dB: 35
    """

    result = parse_cbc_report(sample_text)
    print(result)