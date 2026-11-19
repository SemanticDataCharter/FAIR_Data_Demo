"""Side-by-side: the tutorial's EDA pipeline vs the same agents over a governed model's description.
Variable: BRFSS 2022 MENTHLTH (days mental health not good, past 30). Same model, seed and temperature for both.
Usage: python run.py /path/to/LLCP2022.csv   (needs pandas and a local Ollama with the model pulled)"""
import json, sys, urllib.request
import pandas as pd

MODEL, SEED = "gemma4:12b-it-qat", 42
CSV = sys.argv[1]

def llm(prompt):
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False, "think": False,
                       "options": {"temperature": 0, "seed": SEED, "num_ctx": 8192}}).encode()
    r = urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/generate", body,
                               {"Content-Type": "application/json"}), timeout=900)
    return json.load(r)["response"]

df = pd.read_csv(CSV, usecols=["_STATE", "SEXVAR", "MENTHLTH"])
out = {"model": MODEL, "seed": SEED, "rows": len(df)}

# ---- A: the tutorial as published (blueprint = columns, dtypes, missing counts, shape) ----
schema_info = {"columns": df.columns.tolist(), "dtypes": df.dtypes.astype(str).to_dict(),
               "missing_values": df.isnull().sum().to_dict(), "shape": df.shape}
coder_a = f"""You are a data scientist.
Here is dataset metadata:
{schema_info}
Write Python code using pandas, matplotlib, and seaborn to:
1. Generate summary statistics
2. Plot distributions for numerical columns
3. Plot correlation heatmap
4. Identify missing values visually
Only return executable Python code."""
desc_a = df.describe(include="all").to_string()
analyst_a = f"""You are a senior data scientist.
Here are summary statistics:
{desc_a}
Provide:
- Key patterns
- Potential data quality issues
- Interesting correlations
- Recommendations for modeling"""
out["A"] = {"blueprint": str(schema_info), "describe": desc_a,
            "coder_output": llm(coder_a), "analyst_output": llm(analyst_a)}

# ---- B: same prompts, blueprint = the governed model's description of MENTHLTH ----
m = df.MENTHLTH
none_days, dont_know, refused, blank = (m == 88).sum(), (m == 77).sum(), (m == 99).sum(), m.isna().sum()
valid = m.where(m.between(0, 30) | (m == 88)).replace(88, 0).dropna()
model = {"label": "Days Mental Health Not Good, Past 30 (MENTHLTH)", "type": "XdCount", "units": "days",
         "meaning": "number of days in the past 30 the respondent's mental health was not good",
         "valid_range": "0 to 30 inclusive", "stated_none": "source code 88 is recorded as 0 days",
         "typed_absences": {"don't know (source code 77, ISO 21090 ASKU)": int(dont_know),
                            "refused (source code 99, ISO 21090 ASKR)": int(refused),
                            "not asked / no value": int(blank)}}
desc_b = valid.describe().to_string()
blueprint_b = json.dumps({"columns": {"MENTHLTH": model, "SEXVAR": "sex of respondent (coded)", "_STATE": "state FIPS code"},
                          "shape": list(df.shape)}, indent=1)
coder_b = coder_a.replace(str(schema_info), blueprint_b)
analyst_b = f"""You are a senior data scientist.
Here are summary statistics for MENTHLTH, computed over answered values only (typed absences are excluded by type and counted below):
{desc_b}
Absences by type: {json.dumps(model['typed_absences'])}
Model description: {json.dumps(model)}
Provide:
- Key patterns
- Potential data quality issues
- Interesting correlations
- Recommendations for modeling"""
out["B"] = {"blueprint": blueprint_b, "describe": desc_b, "coder_output": llm(coder_b), "analyst_output": llm(analyst_b)}

out["ground_truth"] = {"raw_mean_all_codes": float(m.mean()), "governed_mean": float(valid.mean()),
                       "n_answered": int(valid.size), "stated_none_88": int(none_days), "dont_know_77": int(dont_know),
                       "refused_99": int(refused), "no_value": int(blank)}
json.dump(out, open("results.json", "w"), indent=1)
for k in "AB":
    open(f"pipeline-{k}-analyst.md", "w").write(out[k]["analyst_output"])
    open(f"pipeline-{k}-coder.py.txt", "w").write(out[k]["coder_output"])
print(json.dumps(out["ground_truth"], indent=1)); print(desc_a); print(desc_b)
