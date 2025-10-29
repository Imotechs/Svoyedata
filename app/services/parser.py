import pandas as pd
import re
import httpx
from io import BytesIO
import logging
from bs4 import BeautifulSoup
import io

HEADER_MAP = {
    # Old ones (existing)
    "number of operating credit institutions": "operating_credit_institutions",
    "number of credit institutions granting housing loans": "institutions_granting_housing_loans",
    "number of credit institutions granting mortgage loans": "institutions_granting_mortgage_loans",
    "number of credit institutions granting mortgage loans against the pledge of claims under share construction participation agreements":
        "institutions_granting_mortgage_loans_under_share_construction",
    "number of credit institutions acquiring claims on mortgage loans": "institutions_acquiring_mortgage_claims",
    "number of credit institutions refinancing previously granted mortgage loans": "institutions_refinancing_mortgage_loans",
    "number of credit institutions refinancing loans on the secondary mortgage loan market":
        "institutions_refinancing_secondary_market",
    "number of credit institutions granting mortgage loans for purchasing and creating individual housing construction objects":
        "institutions_granting_mortgage_loans_for_individual_housing",
    "number of credit institutions transferring rights of mortgage loans":
        "institutions_transferring_rights_of_mortgage_loans",
}


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    normalized = []
    for col in df.columns:
        c = str(col).lower().strip().replace("\n", " ")
        c = " ".join(c.split())  # remove double spaces
        normalized.append(HEADER_MAP.get(c, c))  
    df.columns = normalized
    return df



def parse_excel(file_bytes: bytes) -> pd.DataFrame:
    """Robust parser for Bank of Russia XLSX files (auto-detect header row)."""
    buf = io.BytesIO(file_bytes)
    
    # Read all rows first to locate header
    preview = pd.read_excel(buf, sheet_name="Data", header=None, engine="openpyxl")
    header_row = None
    for i, row in preview.iterrows():
        joined = " ".join(str(x).lower() for x in row if isinstance(x, str))
        if "number of operating credit institutions" in joined:
            header_row = i
            break
    if header_row is None:
        raise ValueError("Header row not found in Excel file.")

    # Re-read file using the detected header row
    buf.seek(0)
    df = pd.read_excel(buf, sheet_name="Data", header=header_row, engine="openpyxl")

    # Normalize headers
    df = normalize_headers(df)
    df.rename(columns={df.columns[0]: "region"}, inplace=True)
    df = df.dropna(subset=["region"])

    # Detect federal districts
    df["is_district"] = df.iloc[:, 1:].isna().all(axis=1)
    df["federal_district"] = None
    current_district = None
    for i, row in df.iterrows():
        if row["is_district"]:
            current_district = row["region"]
        else:
            df.at[i, "federal_district"] = current_district
    df = df[~df["is_district"]].drop(columns=["is_district"])

    # Convert numeric columns
    for c in df.columns:
        if c not in ["region", "federal_district"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df