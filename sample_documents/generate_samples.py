"""
Generate realistic sample documents for DocuMind AI evaluation and testing.
Creates 5 multi-page PDF documents:
1. acme_q3_financial_report.pdf
2. acme_q4_financial_report.pdf
3. acme_remote_work_policy_2023.pdf
4. acme_remote_work_policy_2024.pdf
5. documind_ai_technical_whitepaper.pdf
"""

import os
import fitz  # PyMuPDF

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_header(page, title, subtitle, page_num, total_pages):
    # Top banner line
    page.draw_rect(fitz.Rect(50, 40, 545, 42), color=(0.15, 0.25, 0.5), fill=(0.15, 0.25, 0.5))
    page.insert_text(fitz.Point(50, 32), "DOCUMIND ENTERPRISE CORPUS", fontsize=8, color=(0.4, 0.4, 0.5))
    page.insert_text(fitz.Point(50, 65), title, fontsize=16, fontname="helv", color=(0.1, 0.15, 0.3))
    if subtitle:
        page.insert_text(fitz.Point(50, 82), subtitle, fontsize=10, fontname="helv", color=(0.4, 0.45, 0.55))
    
    # Bottom footer
    page.draw_line(fitz.Point(50, 770), fitz.Point(545, 770), color=(0.8, 0.8, 0.8), width=0.5)
    page.insert_text(fitz.Point(50, 785), "Confidential - For Internal Use Only", fontsize=8, color=(0.5, 0.5, 0.5))
    page.insert_text(fitz.Point(470, 785), f"Page {page_num} of {total_pages}", fontsize=8, color=(0.5, 0.5, 0.5))


def build_q3_report():
    doc = fitz.open()
    
    # Page 1: Financial Overview
    p1 = doc.new_page(width=595, height=842)
    create_header(p1, "Acme Technologies, Inc. - Q3 2024 Financial Report", "Quarter Ended September 30, 2024", 1, 2)
    
    text_p1 = """
1. EXECUTIVE SUMMARY & FINANCIAL HIGHLIGHTS

Acme Technologies, Inc. delivered strong operational performance in the third quarter of fiscal year 2024, driven by accelerated cloud enterprise adoption and expanded platform services.

Key Financial Results for Q3 2024:
- Total Revenue: $42.5 million, representing a 28% year-over-year increase compared to Q3 2023.
- Gross Margin: 74.2%, up 180 basis points compared to the prior quarter.
- Net Income: $8.2 million, compared to $5.9 million in the corresponding period last year.
- Operating Cash Flow: $11.4 million.
- Total Headcount: 480 full-time employees globally as of September 30, 2024.

2. OPERATING EXPENSES BREAKDOWN

The company continued disciplined investments in engineering and go-to-market execution:
- Research and Development (R&D): $12.1 million, focused on scalable vector search and natural language processing pipelines.
- Sales and Marketing (S&M): $14.8 million, driven by North America enterprise sales team expansion.
- General and Administrative (G&A): $6.2 million.

Management reaffirmed guidance for sustained profitability heading into the final quarter of 2024.
"""
    p1.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p1.strip(), fontsize=10, fontname="helv")
    
    # Page 2: Product & Customer Metrics
    p2 = doc.new_page(width=595, height=842)
    create_header(p2, "Acme Technologies, Inc. - Q3 2024 Financial Report", "Products, Operations, and Customer Success", 2, 2)
    
    text_p2 = """
3. PRODUCT PERFORMANCE & CLOUDSCALE ADOPTION

On August 15, 2024, Acme Technologies officially launched its flagship enterprise product line: CloudScale Intelligence Suite. 

CloudScale Metrics for Q3:
- CloudScale Annual Recurring Revenue (ARR): Reached $15 million within its first six weeks of general availability.
- Enterprise Customers: 142 enterprise customers signed contracts with average annual contract value (ACV) of $105,000.
- Platform Uptime: Maintained 99.98% platform service availability across all regions.

4. CUSTOMER RETENTION & EXPANSION

Customer retention metrics remained strong throughout the quarter:
- Enterprise Net Revenue Retention: 118% across recurring enterprise accounts.
- Enterprise Customer Retention Rate: Stood at 94.0% at the close of Q3 2024.
- Customer Satisfaction (CSAT): Measured at 4.7 out of 5.0 across resolved support tickets.

5. BALANCE SHEET AND LIQUIDITY
Cash, cash equivalents, and short-term marketable securities totaled $68.4 million with zero outstanding long-term debt obligations.
"""
    p2.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p2.strip(), fontsize=10, fontname="helv")
    
    out_path = os.path.join(SAMPLE_DIR, "acme_q3_financial_report.pdf")
    doc.save(out_path)
    doc.close()
    print(f"Generated: {out_path}")


def build_q4_report():
    doc = fitz.open()
    
    # Page 1: Financial Performance
    p1 = doc.new_page(width=595, height=842)
    create_header(p1, "Acme Technologies, Inc. - Q4 2024 Financial Report", "Quarter and Fiscal Year Ended December 31, 2024", 1, 2)
    
    text_p1 = """
1. EXECUTIVE SUMMARY & FULL-YEAR FISCAL HIGHLIGHTS

Acme Technologies completed a landmark fiscal year 2024, exceeding operational targets across all core segments.

Key Financial Results for Q4 2024:
- Q4 Total Revenue: $48.0 million, an increase of 12.9% sequentially from Q3 2024.
- Full-Year 2024 Revenue: Total annual revenue reached $175.2 million, up 31% year-over-year.
- Q4 Net Income: $9.5 million, an increase from $8.2 million reported in Q3 2024.
- Operating Cash Flow for Q4: $14.1 million.
- Ending Headcount: 520 full-time employees as of December 31, 2024 (net addition of 40 employees during Q4).

2. OPERATING EXPENSES BREAKDOWN FOR Q4

- Research and Development (R&D): $14.3 million in Q4 (bringing total second-half R&D expenditure to $26.4 million across Q3 and Q4).
- Sales and Marketing (S&M): $16.5 million.
- General and Administrative (G&A): $6.8 million.

The company's operating margin expanded to 21.8%, reflecting improved operational leverage.
"""
    p1.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p1.strip(), fontsize=10, fontname="helv")
    
    # Page 2: Product & Customer Metrics
    p2 = doc.new_page(width=595, height=842)
    create_header(p2, "Acme Technologies, Inc. - Q4 2024 Financial Report", "Products, Operations, and Customer Success", 2, 2)
    
    text_p2 = """
3. CLOUDSCALE PERFORMANCE AND BUSINESS MOMENTUM

The CloudScale Intelligence Suite continued rapid growth in the fourth quarter:
- CloudScale Ending ARR: Reached $22 million by December 31, 2024 (growth of $7 million compared to Q3 ARR of $15 million).
- Key Drivers: Growth was propelled by accelerated enterprise customer migration, expansion of multi-cloud connectors, and new AI workload optimizations.
- Total Active Enterprise Accounts: Increased to 188 active enterprise accounts.

4. CUSTOMER RETENTION AND MARKET OBSERVATIONS

- Enterprise Retention Rate: Decreased slightly to 91.5% in Q4 2024 (down from 94.0% in Q3 2024), primarily due to corporate consolidations and mergers among early-stage tech customers.
- Enterprise Net Expansion Rate: Remained healthy at 116%.
- Gross Margin for Cloud Services: Expanded to 76.0%.

5. FISCAL POSITION
Total cash reserves and equivalents stood at $77.8 million at year-end. Note: Forward-looking financial guidance for Q1 2025 is deferred until the annual investor conference.
"""
    p2.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p2.strip(), fontsize=10, fontname="helv")
    
    out_path = os.path.join(SAMPLE_DIR, "acme_q4_financial_report.pdf")
    doc.save(out_path)
    doc.close()
    print(f"Generated: {out_path}")


def build_policy_2023():
    doc = fitz.open()
    
    # Page 1: Guidelines and Hours
    p1 = doc.new_page(width=595, height=842)
    create_header(p1, "Acme Global Remote Work & Travel Policy", "Version 1.4 - Effective Date: January 1, 2023", 1, 2)
    
    text_p1 = """
1. PURPOSE AND SCOPE

This policy outlines guidelines, benefits, and travel stipulations for remote and hybrid employees at Acme Technologies. This policy applies to all full-time exempt and non-exempt employees globally.

2. CORE WORKING HOURS AND AVAILABILITY

To maintain cross-functional collaboration and business alignment:
- Designated Core Working Hours: All remote team members must be online and available between 10:00 AM - 4:00 PM EST, Monday through Friday.
- Response Expectations: Slack messages during core hours should be acknowledged within 60 minutes. Email messages should be responded to within 24 business hours.
- Meeting Culture: Wednesday afternoons from 1:00 PM to 5:00 PM EST are designated as Focus Blocks, with no scheduled internal company meetings.
"""
    p1.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p1.strip(), fontsize=10, fontname="helv")
    
    # Page 2: Stipends, Travel, and International Work
    p2 = doc.new_page(width=595, height=842)
    create_header(p2, "Acme Global Remote Work & Travel Policy", "Stipends, Travel Reimbursement, and International Remote Work", 2, 2)
    
    text_p2 = """
3. HOME OFFICE STIPEND AND EQUIPMENT

Acme provides financial assistance to support ergonomic remote workspaces:
- Annual Home Office Stipend: Each eligible remote employee receives an annual stipend of $1,200 per calendar year to purchase office furniture, monitors, keyboards, and broadband internet.
- Company Hardware: Standard issue MacBook Pro M2 or ThinkPad P1 is refreshed every 36 months.

4. CORPORATE TRAVEL REIMBURSEMENT LIMITS

- Daily Travel Expenses: The maximum allowable daily reimbursement for lodging and meals without VP approval is $500 per day.
- Approval Threshold: Any business travel expense exceeding $500 per day requires prior written approval from the Department Vice President.

5. INTERNATIONAL REMOTE WORK ALLOWANCE

- Maximum Annual Days: Employees in good standing may work remotely from foreign countries for a maximum of 30 days per calendar year.
- Compliance: Security verification and VPN compliance checks must be completed 14 days prior to international travel.
"""
    p2.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p2.strip(), fontsize=10, fontname="helv")
    
    out_path = os.path.join(SAMPLE_DIR, "acme_remote_work_policy_2023.pdf")
    doc.save(out_path)
    doc.close()
    print(f"Generated: {out_path}")


def build_policy_2024():
    doc = fitz.open()
    
    # Page 1: Guidelines and Hours
    p1 = doc.new_page(width=595, height=842)
    create_header(p1, "Acme Global Remote Work & Travel Policy", "Version 2.0 - Effective Date: January 1, 2024", 1, 2)
    
    text_p1 = """
1. PURPOSE AND SCOPE (UPDATED 2024 REVISION)

This updated policy supersedes Version 1.4 and reflects modern operational needs, enhanced international flexibility, and revised budget allocations.

2. CORE WORKING HOURS AND AVAILABILITY

To accommodate Pacific and European time zone team members:
- Revised Core Working Hours: All remote team members must be online and available between 9:00 AM - 3:00 PM EST, Monday through Friday.
- Asynchronous First: Teams are encouraged to utilize asynchronous documentation in Notion and Loom rather than mandatory sync meetings.
- Focus Day: Friday is officially a No-Meeting Day company-wide.
"""
    p1.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p1.strip(), fontsize=10, fontname="helv")
    
    # Page 2: Stipends, Travel, and International Work (Intentionally contains changes/conflicts)
    p2 = doc.new_page(width=595, height=842)
    create_header(p2, "Acme Global Remote Work & Travel Policy", "Stipends, Travel Reimbursement, and International Remote Work", 2, 2)
    
    text_p2 = """
3. HOME OFFICE STIPEND AND EQUIPMENT (REVISED)

- Annual Home Office Stipend: Under the 2024 budget guidelines, the annual home office stipend is adjusted to $800 per employee per calendar year (reduced from the previous allocation to redirect funds to co-working day passes).
- Coworking Pass: Employees may expense up to 4 day passes per month at approved flexible spaces.

4. CORPORATE TRAVEL REIMBURSEMENT LIMITS (REVISED)

- Daily Travel Expenses: Reflecting inflationary lodging adjustments, the standard daily reimbursement limit is increased to $650 per day without requiring VP approval.
- VP Approval Requirement: Any travel expenses exceeding $650 per day require prior written authorization from a Vice President.

5. INTERNATIONAL REMOTE WORK ALLOWANCE (EXPANDED)

- Maximum Annual Allowance: Employees may work from approved international jurisdictions for up to 45 days per calendar year (expanded from 30 days under the prior policy).
- Tax and Legal Clearance: Employees must notify People Operations at least 21 days in advance of overseas departure.
"""
    p2.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p2.strip(), fontsize=10, fontname="helv")
    
    out_path = os.path.join(SAMPLE_DIR, "acme_remote_work_policy_2024.pdf")
    doc.save(out_path)
    doc.close()
    print(f"Generated: {out_path}")


def build_whitepaper():
    doc = fitz.open()
    
    # Page 1: Architecture & Retrieval
    p1 = doc.new_page(width=595, height=842)
    create_header(p1, "DocuMind AI Architecture Whitepaper", "Evidence-Grounded RAG & Claim Verification Systems", 1, 2)
    
    text_p1 = """
1. ARCHITECTURAL OVERVIEW

DocuMind AI is an enterprise document intelligence platform engineered for factual precision, verifiable citations, and automated contradiction detection across enterprise document repositories.

2. HYBRID RETRIEVAL PIPELINE

To solve common lexical and semantic search failure modes, DocuMind integrates a multi-stage hybrid retrieval architecture:
- Dense Vector Retrieval: Employs the sentence-transformers 'all-MiniLM-L6-v2' model, generating 384-dimensional dense semantic embeddings with cosine distance metric.
- Sparse Keyword Retrieval: Utilizes BM25 (Best Matching 25) indexing with calibrated hyperparameters k1 = 1.5 and b = 0.75.
- Reciprocal Rank Fusion (RRF): Combines dense and sparse rank lists using the formula:
    RRF_Score(d) = Sum_{m in M} (1 / (k + rank_m(d)))
  where default fusion constant k = 60.
- Deduplication and Chunk Preservation: Preserves page numbers, character spans, and document IDs across all retrieved segments.
"""
    p1.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p1.strip(), fontsize=10, fontname="helv")
    
    # Page 2: Reranking & Verification
    p2 = doc.new_page(width=595, height=842)
    create_header(p2, "DocuMind AI Architecture Whitepaper", "Cross-Encoder Reranking and Claim Verification", 2, 2)
    
    text_p2 = """
3. CROSS-ENCODER RERANKING

Top-30 candidate passages from RRF fusion are passed through an optional cross-encoder reranking model:
- Model Architecture: ms-marco-MiniLM-L-6-v2.
- Scoring: Computes joint query-passage cross-attention scores to refine the top-5 to top-10 context passages passed to the generator.

4. VECTOR STORAGE CONFIGURATION

- Vector Engine: ChromaDB persistent vector database.
- Similarity Metric: Cosine distance (1 - cosine_similarity).
- Sharding & Metadata: Page number, chunk index, document hash, and collection ID stored in indexed metadata attributes.

5. EVIDENCE VERIFICATION ENGINE

The verification engine decomposes generated responses into atomic factual claims. Each claim is evaluated against source passages:
- Supported: Evidence directly entails the claim.
- Partially Supported: Evidence supports part of the claim or introduces minor qualification.
- Contradicted: Evidence directly refutes or contradicts the claim.
- Not Supported: Evidence does not contain sufficient information to prove the claim.

6. CROSS-DOCUMENT CONFLICT DETECTION
The engine performs pairwise statement comparison across multi-version documents to flag divergent dates, numbers, and policies.
"""
    p2.insert_textbox(fitz.Rect(50, 100, 545, 750), text_p2.strip(), fontsize=10, fontname="helv")
    
    out_path = os.path.join(SAMPLE_DIR, "documind_ai_technical_whitepaper.pdf")
    doc.save(out_path)
    doc.close()
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    print("Generating sample documents...")
    build_q3_report()
    build_q4_report()
    build_policy_2023()
    build_policy_2024()
    build_whitepaper()
    print("All sample documents successfully generated.")
