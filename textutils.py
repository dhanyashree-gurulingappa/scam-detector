import re


def normalize(text):
    t = str(text)
    t = re.sub(
        r"(https?://\S+|www\.\S+|\b(?:[\w-]+\.)+(?:com|in|co|me|ly|link|xyz|top|app|net|org)\b(?:/\S*)?)",
        " <URL> ", t, flags=re.IGNORECASE)
    t = re.sub(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)", " <PHONE> ", t)
    t = re.sub(r"(?:rs\.?|inr|₹)\s?[\d,]+(?:\.\d+)?", " <AMOUNT> ", t, flags=re.IGNORECASE)
    t = re.sub(r"\d{4,}", " <NUM> ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t
