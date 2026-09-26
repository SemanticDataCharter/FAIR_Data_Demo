"""
CMS Prescription Drug Event 4.2.0: one record per DE-SynPUF Part D event row (2008-2010) of a sampled beneficiary.

The product is the National Drug Code as a coded value; quantity, days supply and the amounts as recorded.
The file has 5.5 million rows and is streamed.
"""
import re
import time

from cms_common import AGENCY, SUBJECT, sample_ids, usd
from shared import Quantity, cms_date, import_dir, read_csv, record, write_record

TITLE = "CMS Prescription Drug Event"
OUTPUT_DIR = import_dir("cms_prescription_drug_event")
NDC_RE = re.compile(r"^[0-9]{11}$")


def build_instance(row: dict, left: dict) -> str:
    ndc = row["PROD_SRVC_ID"]
    if ndc and ndc.isdigit() and len(ndc) < 11:
        ndc = ndc.zfill(11); left["ndc padded"] = left.get("ndc padded", 0) + 1
    if ndc and not NDC_RE.match(ndc):
        left["ndc left out"] = left.get("ndc left out", 0) + 1; ndc = None
    qty_v = row["QTY_DSPNSD_NUM"]
    values = {
        "Beneficiary Code (DESYNPUF_ID)": row["DESYNPUF_ID"],
        "Prescription Drug Event ID (PDE_ID)": row["PDE_ID"] if row["PDE_ID"].isdigit() else None,
        "Service Date (SRVC_DT)": cms_date(row["SRVC_DT"]),
        "Product (NDC)/Product Service ID (NDC)": ndc or None,
        "Quantity Dispensed (QTY_DSPNSD_NUM)": Quantity(qty_v, "items") if qty_v else None,
        "Days Supply (DAYS_SUPLY_NUM)": Quantity(row["DAYS_SUPLY_NUM"], "days") if row["DAYS_SUPLY_NUM"].isdigit() else None,
        "Patient Pay Amount": usd(row["PTNT_PAY_AMT"]),
        "Total Prescription Cost": usd(row["TOT_RX_CST_AMT"]),
    }
    return record(TITLE, values, study="CMS", agency=AGENCY, source_key="CMS_PDE", subject=(SUBJECT, row["DESYNPUF_ID"]), row_ref=f"PDE_ID={row['PDE_ID']}")


def generate():
    t0 = time.time()
    keep = sample_ids()
    left = {}
    count = 0
    for row in read_csv("CMS_PDE"):
        if row["DESYNPUF_ID"] not in keep:
            continue
        write_record(OUTPUT_DIR, "cp", build_instance(row, left))
        count += 1
    print(f"CMS Prescription Drug Event: generated {count} XML files in {OUTPUT_DIR} ({time.time() - t0:.1f}s); {left}")
    return count


if __name__ == "__main__":
    generate()
