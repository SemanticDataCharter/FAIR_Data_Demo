# Side-by-side: a 9 is nine days (MENTHLTH)

Same local model (`gemma4:12b-it-qat` via Ollama), temperature 0, seed 42, same prompt templates. The blueprint differs, and B's analyst prompt also carries the model description and absence counts.

- **A:** the tutorial's pipeline as published (amanxai.com, 4 March 2026): columns, dtypes, missing counts and shape as the blueprint; `df.describe(include="all")` to the analyst.
- **B:** the governed model's description of MENTHLTH (meaning, units, 0 to 30, source code 88 stated as 0 days, typed absences ASKU/ASKR/not asked, counted); `describe()` over answered values only.

Data: BRFSS 2022 `LLCP2022.csv` (445,132 rows), from the FAIR Data Demo's `source_data/brfss/`.

Run: `python run.py /path/to/LLCP2022.csv` (pandas + Ollama with the model pulled). Outputs: `results.json`, `pipeline-{A,B}-analyst.md`, `pipeline-{A,B}-coder.py.txt`.

Limits: one run, three columns (`_STATE`, `SEXVAR`, `MENTHLTH`; all 326 would not fit the context), LLM text varies by model and version. The tutorial prints the coder agent's code without running it; so do we. The mapping in B (88 to 0, 77 and 99 to typed absences) is written into the model, not inferred by the LLM.

Data: the CSV comes from the demo's own conversion step (`scripts/convert_xpt_to_csv.py`) on `source_data/brfss/LLCP2022.XPT`; see `source_data/README.md` for the download. Example: `python examples/menthlth-side-by-side/run.py source_data/brfss/LLCP2022.csv` from the repository root, run inside the example folder so the outputs land there.
