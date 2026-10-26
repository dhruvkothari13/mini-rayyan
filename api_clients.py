"""
STAGE 2: PubMed E-utilities & Europe PMC API Clients (api_clients.py)
Fetches live hit counts and full metadata + abstracts from PubMed and Europe PMC.
Also provides a rich 20-record benchmark dataset for testing all edge cases.
"""

import os
import re
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Any
import requests 

NCBI_TOOL_NAME = os.environ.get("NCBI_TOOL_NAME", "mini_rayyan_hackathon_tool")
NCBI_EMAIL = os.environ.get("NCBI_EMAIL", "researcher@university.edu")
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")


def normalize_title(title: str) -> str:
    """Normalize title for duplicate comparison: lowercase, strip punctuation & extra whitespace."""
    if not title:
        return ""
    cleaned = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def extract_first_author_surname(authors_str: str) -> str:
    """Extract normalized surname of the first author."""
    if not authors_str:
        return ""
    first = authors_str.split(",")[0].split(";")[0].strip().lower()
    parts = first.split()
    return parts[0] if parts else ""


# ==============================================================================
# 1. PUBMED E-UTILITIES API CLIENT
# ==============================================================================
def search_pubmed_hits(boolean_query: str, date_from: int, date_to: int, max_fetch: int = 100) -> Tuple[int, List[str], str]:
    """
    Run ESearch on PubMed to get total hit count and up to `max_fetch` PMIDs.
    Returns (total_hit_count, list_of_pmids, error_message_if_any).
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": boolean_query,
        "mindate": f"{date_from}/01/01",
        "maxdate": f"{date_to}/12/31",
        "datetype": "pdat",
        "retmode": "json",
        "retmax": max_fetch,
        "tool": NCBI_TOOL_NAME,
        "email": NCBI_EMAIL,
    }
    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    try:
        resp = requests.get(base_url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("esearchresult", {})
        if "ERROR" in data:
            return 0, [], f"PubMed API Error: {data['ERROR']}"
        count = int(data.get("count", 0))
        id_list = data.get("idlist", [])
        return count, id_list, ""
    except Exception as e:
        return 0, [], f"PubMed search failed: {str(e)}"


def fetch_pubmed_abstracts(pmids: List[str]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Fetch full records (Title, Abstract, Authors, Year, Journal, DOI, PMID,
    Language, Publication Types) from PubMed EFetch in batches of 50.
    Respects NCBI rate limits (3 req/s without key).
    """
    if not pmids:
        return [], ""

    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    records: List[Dict[str, Any]] = []
    batch_size = 50
    delay = 0.12 if NCBI_API_KEY else 0.35

    try:
        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
                "tool": NCBI_TOOL_NAME,
                "email": NCBI_EMAIL,
            }
            if NCBI_API_KEY:
                params["api_key"] = NCBI_API_KEY

            resp = requests.get(base_url, params=params, timeout=25)
            resp.raise_for_status()

            root = ET.fromstring(resp.content)
            for article in root.findall(".//PubmedArticle"):
                pmid_el = article.find(".//MedlineCitation/PMID")
                pmid = pmid_el.text.strip() if pmid_el is not None and pmid_el.text else ""

                title_el = article.find(".//Article/ArticleTitle")
                title = "".join(title_el.itertext()).strip() if title_el is not None else "Untitled Study"

                # Combine structured abstract sections if present
                abs_texts = []
                for abs_el in article.findall(".//Article/Abstract/AbstractText"):
                    label = abs_el.attrib.get("Label", "")
                    txt = "".join(abs_el.itertext()).strip()
                    if txt:
                        abs_texts.append(f"{label}: {txt}" if label else txt)
                abstract = " ".join(abs_texts)

                # Authors
                authors_list = []
                for auth in article.findall(".//Article/AuthorList/Author"):
                    last = auth.findtext("LastName", "").strip()
                    init = auth.findtext("Initials", "").strip()
                    if last:
                        authors_list.append(f"{last} {init}".strip())
                authors_str = ", ".join(authors_list)
                first_author = authors_list[0].split()[0].lower() if authors_list else ""

                # Publication Year
                year_str = (
                    article.findtext(".//Article/Journal/JournalIssue/PubDate/Year")
                    or article.findtext(".//Article/Journal/JournalIssue/PubDate/MedlineDate", "")[:4]
                )
                pub_year = int(year_str) if year_str and year_str.isdigit() else None

                journal = article.findtext(".//Article/Journal/Title", "").strip()
                pages = article.findtext(".//Article/Pagination/MedlinePgn", "").strip()
                lang = article.findtext(".//Article/Language", "eng").strip().lower()

                # Publication Types (e.g., Clinical Trial, Case Reports, Review)
                pub_types = [
                    pt.text.strip()
                    for pt in article.findall(".//Article/PublicationTypeList/PublicationType")
                    if pt.text
                ]

                # DOI
                doi = ""
                for id_el in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                    if id_el.attrib.get("IdType") == "doi" and id_el.text:
                        doi = id_el.text.strip().lower()
                        break

                records.append({
                    "pmid": pmid,
                    "doi": doi,
                    "title": title,
                    "norm_title": normalize_title(title),
                    "abstract": abstract,
                    "authors": authors_str,
                    "first_author": first_author,
                    "pub_year": pub_year,
                    "journal": journal,
                    "pages": pages,
                    "language": lang,
                    "pub_types": ", ".join(pub_types) if pub_types else "Journal Article",
                    "source": "PubMed",
                })
            time.sleep(delay)
        return records, ""
    except Exception as e:
        return records, f"PubMed EFetch error: {str(e)}"


# ==============================================================================
# 2. EUROPE PMC REST API CLIENT
# ==============================================================================
def build_epmc_query(boolean_query: str, date_from: int, date_to: int) -> str:
    return f"({boolean_query}) AND (FIRST_PDATE:[{date_from}-01-01 TO {date_to}-12-31])"


def search_epmc_hits(boolean_query: str, date_from: int, date_to: int) -> Tuple[int, str]:
    """Query Europe PMC REST API for hit count."""
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": build_epmc_query(boolean_query, date_from, date_to),
        "format": "json",
        "pageSize": 1,
        "synonym": "false",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return int(data.get("hitCount", 0)), ""
    except Exception as e:
        return 0, f"Europe PMC search error: {str(e)}"


def fetch_epmc_abstracts(boolean_query: str, date_from: int, date_to: int, max_fetch: int = 100) -> Tuple[List[Dict[str, Any]], str]:
    """
    Fetch up to `max_fetch` core records from Europe PMC REST API.
    Europe PMC returns up to 100 records per page by default.
    """
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": build_epmc_query(boolean_query, date_from, date_to),
        "resultType": "core",
        "format": "json",
        "pageSize": min(max_fetch, 100),
        "synonym": "false",
    }
    records: List[Dict[str, Any]] = []
    try:
        resp = requests.get(url, params=params, timeout=25)
        resp.raise_for_status()
        results = resp.json().get("resultList", {}).get("result", [])
        for item in results[:max_fetch]:
            title = (item.get("title") or "Untitled Study").strip()
            abstract = (item.get("abstractText") or "").strip()
            # Clean inline HTML tags occasionally present in Europe PMC abstracts
            abstract = re.sub(r"<[^>]+>", " ", abstract)
            abstract = re.sub(r"\s+", " ", abstract).strip()

            authors_str = (item.get("authorString") or "").strip()
            first_author = extract_first_author_surname(authors_str)
            year_str = str(item.get("pubYear") or "")
            pub_year = int(year_str) if year_str.isdigit() else None

            journal_info = item.get("journalInfo", {}).get("journal", {})
            journal = journal_info.get("title") or item.get("journalTitle") or ""
            pages = item.get("pageInfo") or ""
            lang = (item.get("language") or "eng").strip().lower()

            pub_type_list = item.get("pubTypeList", {}).get("pubType", [])
            if isinstance(pub_type_list, list):
                pub_types = ", ".join(str(x) for x in pub_type_list)
            else:
                pub_types = str(pub_type_list or "Journal Article")

            records.append({
                "pmid": str(item.get("pmid") or "").strip(),
                "doi": str(item.get("doi") or "").strip().lower(),
                "title": title,
                "norm_title": normalize_title(title),
                "abstract": abstract,
                "authors": authors_str,
                "first_author": first_author,
                "pub_year": pub_year,
                "journal": journal,
                "pages": pages,
                "language": lang,
                "pub_types": pub_types,
                "source": "Europe PMC",
            })
        return records, ""
    except Exception as e:
        return records, f"Europe PMC fetch error: {str(e)}"


# ==============================================================================
# 3. BENCHMARK DATASET (20 Realistic Papers Covering All Hackathon Test Cases)
# ==============================================================================
def get_benchmark_papers(variant: str = "v1") -> List[Dict[str, Any]]:
    """
    Provides realistic clinical abstracts so the team can test:
    - Exact DOI/PMID duplicates across PubMed & Europe PMC
    - Missing-DOI fuzzy duplicates (Title + Year + First Author match)
    - Conference version vs. Journal paper of the same study (Must NOT auto-hide)
    - Animal studies (rat/murine), Simulation studies (Monte Carlo/in-silico),
      Non-English papers (German/French), Case reports, and eligible RCTs.
    """
    base_papers = [
        # 1 & 2: Exact DOI duplicate across PubMed and Europe PMC
        {
            "pmid": "34001001", "doi": "10.1056/nejmoa2021001",
            "title": "Efficacy of Metformin versus Placebo on Glycemic Control in Adults with Type 2 Diabetes: A Randomized Controlled Trial",
            "abstract": "BACKGROUND: Optimal first-line therapy remains essential. METHODS: Adults with type 2 diabetes (n=420) received metformin 1000 mg twice daily or matching placebo for 24 weeks. RESULTS: The primary outcome was change in HbA1c from baseline, which decreased by -1.2% in the metformin group compared with -0.2% in the placebo group (p<0.001).",
            "authors": "Anderson K, Patel R, Gomez L", "first_author": "anderson",
            "pub_year": 2021, "journal": "New England Journal of Medicine", "pages": "112-120",
            "language": "eng", "pub_types": "Randomized Controlled Trial, Journal Article", "source": "PubMed"
        },
        {
            "pmid": "34001001", "doi": "10.1056/nejmoa2021001",
            "title": "Efficacy of Metformin versus Placebo on Glycemic Control in Adults with Type 2 Diabetes: A Randomized Controlled Trial.",
            "abstract": "Adults with type 2 diabetes (n=420) received metformin 1000 mg twice daily or matching placebo for 24 weeks. The primary outcome was change in HbA1c from baseline, which decreased by -1.2% in the metformin group compared with -0.2% in the placebo group.",
            "authors": "Anderson K, Patel R, Gomez L", "first_author": "anderson",
            "pub_year": 2021, "journal": "N Engl J Med", "pages": "112-120",
            "language": "eng", "pub_types": "Journal Article", "source": "Europe PMC"
        },
        # 3 & 4: Missing DOI on one record -> Fuzzy match on Title + Year + First Author
        {
            "pmid": "35112002", "doi": "10.2337/dc22-0411",
            "title": "Comparative Effectiveness of Metformin and Glimepiride in Newly Diagnosed Type 2 Diabetes Patients",
            "abstract": "In this multicenter trial, 310 adult patients with newly diagnosed type 2 diabetes were assigned to oral metformin (1500 mg/day) or sulfonylurea comparator glimepiride (4 mg/day) for 16 weeks. The primary outcome was reduction in glycated haemoglobin (HbA1c) and fasting blood glucose.",
            "authors": "Chen W, Liu Y, Zhang H", "first_author": "chen",
            "pub_year": 2022, "journal": "Diabetes Care", "pages": "889-897",
            "language": "eng", "pub_types": "Clinical Trial, Journal Article", "source": "PubMed"
        },
        {
            "pmid": "", "doi": "",
            "title": "Comparative effectiveness of metformin and glimepiride in newly diagnosed type 2 diabetes patients!",
            "abstract": "In this multicenter trial, 310 adult patients with newly diagnosed type 2 diabetes were assigned to oral metformin (1500 mg/day) or sulfonylurea comparator glimepiride (4 mg/day) for 16 weeks. The primary outcome was reduction in glycated haemoglobin (HbA1c) and fasting blood glucose.",
            "authors": "Chen W, Liu Y", "first_author": "chen",
            "pub_year": 2022, "journal": "Diabetes Care", "pages": "889-897",
            "language": "eng", "pub_types": "Journal Article", "source": "Europe PMC"
        },
        # 5 & 6: Further reports of one study (Conference abstract vs Journal article -> Should be flagged Uncertain/Not Auto-Hidden)
        {
            "pmid": "36200105", "doi": "10.1007/s00125-023-05800-1",
            "title": "Long-Term HbA1c Durability with Extended-Release Metformin versus Placebo in Overweight Adults with Type 2 Diabetes",
            "abstract": "Overweight adults with type 2 diabetes (n=260) received extended-release metformin or placebo over 52 weeks. Primary outcome was sustained change in HbA1c and body weight.",
            "authors": "Miller T, Roberts S, Kim J", "first_author": "miller",
            "pub_year": 2023, "journal": "Diabetologia", "pages": "410-422",
            "language": "eng", "pub_types": "Randomized Controlled Trial, Journal Article", "source": "PubMed"
        },
        {
            "pmid": "", "doi": "10.1007/s00125-023-conf-99",
            "title": "Long-Term HbA1c Durability with Extended-Release Metformin versus Placebo in Overweight Adults with Type 2 Diabetes",
            "abstract": "Preliminary conference presentation of the 26-week interim analysis: Overweight adults with type 2 diabetes received extended-release metformin or placebo.",
            "authors": "Miller T, Roberts S", "first_author": "miller",
            "pub_year": 2023, "journal": "EASD Annual Meeting Proceedings", "pages": "S45",
            "language": "eng", "pub_types": "Conference Abstract", "source": "Europe PMC"
        },
        # 7: Animal Study (Should be Excluded with reason: non-human/animal)
        {
            "pmid": "33900111", "doi": "10.1210/endocr/bqab012",
            "title": "Hepatic AMPK Activation by Metformin versus Vehicle Placebo in Streptozotocin-Induced Diabetic Wistar Rats",
            "abstract": "Forty male Sprague-Dawley and Wistar rats with streptozotocin-induced diabetes were randomized to oral metformin (200 mg/kg) or saline placebo for 4 weeks. Blood glucose and hepatic gluconeogenesis gene expression were measured in rodent liver tissue.",
            "authors": "Takahashi M, Sato K", "first_author": "takahashi",
            "pub_year": 2021, "journal": "Endocrinology", "pages": "15-24",
            "language": "eng", "pub_types": "Journal Article", "source": "PubMed"
        },
        # 8: Simulation / In-Silico Study (Should be Excluded with reason: simulation)
        {
            "pmid": "34800222", "doi": "10.1016/j.cmpb.2022.106700",
            "title": "In Silico Pharmacokinetic Monte Carlo Simulation of Metformin versus Placebo on HbA1c Trajectories",
            "abstract": "We developed a mathematical Markov model simulation and computer simulation of 10,000 virtual diabetic avatars. No human patients were recruited. Simulated HbA1c curves were projected over 5 years under virtual metformin and placebo regimens.",
            "authors": "Dubois P, Laurent C", "first_author": "dubois",
            "pub_year": 2022, "journal": "Computer Methods and Programs in Biomedicine", "pages": "106700",
            "language": "eng", "pub_types": "Journal Article", "source": "PubMed"
        },
        # 9: Non-English Study (Should be Excluded with reason: non-English)
        {
            "pmid": "32700333", "doi": "10.1055/a-1200-4455",
            "title": "Wirksamkeit von Metformin im Vergleich zu Placebo bei Erwachsenen mit Typ-2-Diabetes: Eine klinische Analyse",
            "abstract": "Hintergrund: Untersuchung der Senkung des HbA1c-Wertes bei erwachsenen Patienten mit Typ-2-Diabetes unter Metformin-Therapie im Vergleich zu Placebo über 12 Wochen.",
            "authors": "Schmidt H, Weber M", "first_author": "schmidt",
            "pub_year": 2020, "journal": "Deutsche Medizinische Wochenschrift", "pages": "901-907",
            "language": "ger", "pub_types": "Journal Article", "source": "PubMed"
        },
        # 10: Case Report (Should be Excluded with reason: case report)
        {
            "pmid": "35900444", "doi": "10.1186/s13256-022-03500-x",
            "title": "Severe Lactic Acidosis Following High-Dose Metformin in a 68-Year-Old Male with Type 2 Diabetes: A Case Report",
            "abstract": "We report a single patient case report. A 68-year-old male presented to the emergency department with nausea and elevated lactate after taking metformin. HbA1c on admission was 8.4%.",
            "authors": "O'Connor D, Murphy B", "first_author": "o'connor",
            "pub_year": 2022, "journal": "Journal of Medical Case Reports", "pages": "214",
            "language": "eng", "pub_types": "Case Reports", "source": "PubMed"
        },
        # 11: Eligible RCT (Clear PICO)
        {
            "pmid": "36500555", "doi": "10.1016/s0140-6736(23)00111-2",
            "title": "Dual Therapy with Metformin vs Placebo Added to Lifestyle Intervention in Adults with Type 2 Diabetes",
            "abstract": "Participants were 512 adults with type 2 diabetes inadequately controlled on diet alone. Patients were randomized to metformin (2000 mg daily) or matching placebo for 26 weeks. The primary outcome was mean change in HbA1c from baseline to week 26 (-1.4% vs -0.3%).",
            "authors": "ramirez j, fernandez a, costa m", "first_author": "ramirez",
            "pub_year": 2023, "journal": "The Lancet", "pages": "1402-1411",
            "language": "eng", "pub_types": "Randomized Controlled Trial", "source": "PubMed"
        },
        # 12: Uncertain / Pilot Study with unclear population (Should be flagged Maybe for Human Review)
        {
            "pmid": "37100666", "doi": "10.1111/dom.15001",
            "title": "Exploratory Biomarker Pilot of Metformin Administration on Glycemic Variability",
            "abstract": "In this small exploratory study (n=18 participants with metabolic syndrome and borderline dysglycemia), short-term metformin was evaluated over 4 weeks. Continuous glucose monitoring metrics were recorded, though no formal comparator arm was prespecified.",
            "authors": "Nguyen T, Park S", "first_author": "nguyen",
            "pub_year": 2024, "journal": "Diabetes, Obesity and Metabolism", "pages": "77-82",
            "language": "eng", "pub_types": "Journal Article", "source": "Europe PMC"
        },
    ]

    if variant == "v2":
        # Additional records returned when user expands query in Level 2 (e.g. adding sulfonylurea / sitagliptin)
        v2_extra = [
            # Bridges / merges with Record #12 or adds new RCTs
            {
                "pmid": "37800777", "doi": "10.2337/dc24-0199",
                "title": "Metformin Compared with Sitagliptin and Glipizide on HbA1c Reduction in Elderly Adults with Type 2 Diabetes",
                "abstract": "Elderly adults with type 2 diabetes (aged 65-80 years, n=380) received metformin 1000 mg/day compared with glipizide or sitagliptin for 36 weeks. Primary outcome was change in HbA1c and hypoglycemia incidence.",
                "authors": "Hassan A, El-Sayed M", "first_author": "hassan",
                "pub_year": 2024, "journal": "Diabetes Care", "pages": "1120-1129",
                "language": "eng", "pub_types": "Randomized Controlled Trial", "source": "PubMed"
            },
            {
                "pmid": "37900888", "doi": "10.1002/dmrr.3600",
                "title": "Murine Islet Beta-Cell Preservation with Metformin and Sulfonylurea Combination in C57BL/6 Mice",
                "abstract": "Diabetic C57BL/6 mice were treated with metformin and glibenclamide in vivo for 6 weeks to evaluate pancreatic beta-cell apoptosis.",
                "authors": "Lin X, Zhou Q", "first_author": "lin",
                "pub_year": 2024, "journal": "Diabetes/Metabolism Research and Reviews", "pages": "e3600",
                "language": "eng", "pub_types": "Journal Article", "source": "Europe PMC"
            }
        ]
        base_papers.extend(v2_extra)

    for p in base_papers:
        p["norm_title"] = normalize_title(p["title"])
    return base_papers