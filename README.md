Mini-Rayyan — An AI Research Assistant for Medical Fact-Checking 

-What Is This Actually About?

Imagine a doctor wants to answer a simple question:
"For adults with Type 2 Diabetes, does Metformin lower blood sugar better than a placebo?"

You can't just trust one study—you have to check all the published medical research to be sure. In medicine, this process is called a Systematic Review. 

The problem? Searching medical libraries like PubMed brings back hundreds or thousands of papers, including:
* The exact same paper showing up twice from different websites.
* Experiments done on rats or computer simulations instead of humans.
* Papers written in other languages or single-patient stories that don't prove anything.

Mini-Rayyan automates the boring, repetitive parts of this process while keeping a human in full control of every final decision. 

-Quick 10-Second Guide: What is "PICO"?

You'll see the word **PICO** inside the app. It’s just a simple checklist doctors use to turn a messy question into 4 clear parts:

* 🟦 P — Population: Who are the patients? (e.g., Adults with Type 2 Diabetes)
* 🟩 I — Intervention: What drug or treatment is being tested? (e.g., Metformin)
* 🟧 C — Comparator: What is it being compared against? (e.g., A sugar pill / Placebo)
* 🟪 O — Outcome: What health result are we measuring? (e.g., Lower blood sugar / HbA1c)

Mini-Rayyan automatically finds and color-highlights these 4 things inside every paper's summary so you don't have to hunt for them.

-How the App Works (Step-by-Step)

1. Pick a Medical Topic (or Type Your Own): Choose from 12 built-in medical topics across 6 specialties (Heart Disease, Diabetes, Cancer, Mental Health, Asthma, Kidney Disease, etc.) or enter your own custom question.
2. Search Real Medical Libraries: The app searches live, free global databases (PubMed** and Europe PMC, with an automatic OpenAlex backup if a server is busy) and pulls the paper summaries.
3. Safe Storage (Zero-Deletion Rule): Everything is saved in a local SQLite database. Nothing is ever permanently deleted—duplicates and rejected papers are just neatly tucked away so you can always double-check or undo anything.
4. Clean Up Duplicates: Automatically hides exact duplicate copies. If two papers look similar but might be different (like a short conference summary vs. a full journal article), it shows both side-by-side and lets **you** decide.
5. Sort Papers into Clear Buckets: Quickly sort studies into **✅ Included**, **❌ Excluded**, or **🤔 Maybe** using a split-screen reader. The app automatically flags animal studies, computer simulations, and non-English papers for you.
6. Update Your Search Anytime (Level-2 Loop): If you edit your search keywords later, the app compares your old search vs. your new search, shows which papers were added or removed, and keeps all your past work intact.
7. Export to Excel / CSV: Download your final verified list of studies—plus a full history log of every edit you made—with one click.

-What Each File Does

| `app.py` | The main web interface, themes,  and AI Lab |
| `database.py` | Saves all papers, decisions, and audit history in SQLite |
| `api_clients.py` | Connects to PubMed, Europe PMC, and stores the offline demo pack |
| `pipeline.py` | Finds duplicate papers and runs the automatic screening rules |
| `pico_extractor.py` | Pulls out the P, I, C, and O phrases from paper summaries |
| `level2_loop.py` | Compares different search versions and flags decision conflicts |
