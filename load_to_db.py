"""
Load Stata data into SQLite database with clean schema.
Creates normalized tables for companies, financials, ownership, market indices, and life stages.
"""

import pandas as pd
import sqlite3
import os

DTA_PATH = os.path.join(os.path.dirname(__file__), "sp401nf24y_furtherEd_oldCLS.dta")
DB_PATH = os.path.join(os.path.dirname(__file__), "capital_structure.db")

def load_data():
    print("Reading Stata file...")
    df = pd.read_stata(DTA_PATH)
    print(f"Loaded {df.shape[0]:,} rows x {df.shape[1]} columns")
    return df

def create_database(df):
    # Remove old DB if exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")

    # ── 1. Companies (dimension table) ──
    cur.execute("""
        CREATE TABLE companies (
            company_code    INTEGER PRIMARY KEY,
            company_name    TEXT NOT NULL,
            nse_symbol      TEXT,
            inc_year        INTEGER,
            industry_group  TEXT,
            industry_group_code REAL,
            industry_type   INTEGER
        )
    """)

    companies = df[["companycode", "companyname", "nsesymbol", "incYr",
                     "industrygroup", "industrygroupcode", "industrytype"]].drop_duplicates("companycode")
    for _, r in companies.iterrows():
        cur.execute(
            "INSERT INTO companies VALUES (?,?,?,?,?,?,?)",
            (int(r.companycode), r.companyname, r.nsesymbol, int(r.incYr),
             r.industrygroup, r.industrygroupcode, int(r.industrytype))
        )
    print(f"  companies: {len(companies)} rows")

    # ── 2. Life stages lookup ──
    # Note: cls78=7 maps to both Decline and Decay, so use stage_name as PK
    cur.execute("""
        CREATE TABLE life_stages (
            stage_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            cls_code    INTEGER,
            stage_name  TEXT NOT NULL UNIQUE
        )
    """)
    stages = df[["cls78", "corplifestage"]].drop_duplicates().sort_values("cls78")
    for _, r in stages.iterrows():
        cur.execute("INSERT INTO life_stages (cls_code, stage_name) VALUES (?,?)",
                    (int(r.cls78), str(r.corplifestage)))
    print(f"  life_stages: {len(stages)} rows")

    # ── 3. Financials (fact table — core panel data) ──
    cur.execute("""
        CREATE TABLE financials (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code    INTEGER NOT NULL,
            year            INTEGER NOT NULL,
            slot_date       TEXT,
            slot_year       TEXT,
            age_group       TEXT,
            size_decile     TEXT,
            cls_code        INTEGER,
            life_stage      TEXT,
            -- Dependent variable
            leverage        REAL,
            lev_pct         REAL,
            -- Key determinants
            profitability   REAL,
            tangibility     REAL,
            tax             REAL,
            dividend        REAL,
            interest        REAL,
            firm_size       REAL,
            log_size        REAL,
            ln_size         REAL,
            tax_shield      REAL,
            log_tax_shield  REAL,
            -- Income statement
            pbit            REAL,
            pbt             REAL,
            interest_amt    REAL,
            -- Balance sheet
            total_capital       REAL,
            reserves_and_funds  REAL,
            borrowings          REAL,
            debentures_bonds    REAL,
            total_liabilities   REAL,
            -- Cash flows
            ncfo            REAL,
            ncfi            REAL,
            ncff            REAL,
            net_cash_flow   REAL,
            ncf_dummy       INTEGER,
            -- Cash holdings
            st_invest       REAL,
            cash_bal        REAL,
            bank_bal        REAL,
            cash_holdings   REAL,
            -- Transformed variables
            prof100         REAL,
            tang100         REAL,
            lev1_100        REAL,
            pbit1           REAL,
            pbt1            REAL,
            intamt1         REAL,
            tax_shield1     REAL,
            log_tax_shield1 REAL,
            log_tang        REAL,
            -- Life stage dummies
            oc              INTEGER,
            ic              INTEGER,
            fc              INTEGER,
            -- Event dummies
            gfc             INTEGER,
            ibc_2016        INTEGER,
            ibc_2016_20     INTEGER,
            covid_dummy     INTEGER,
            -- Interest rates
            int_rate        REAL,
            int_rate_lt     REAL,
            FOREIGN KEY (company_code) REFERENCES companies(company_code)
        )
    """)

    fin_cols_map = {
        "companycode": "company_code", "year": "year", "slotdate": "slot_date",
        "slotyear": "slot_year", "agegroup": "age_group", "sizedecile": "size_decile",
        "cls78": "cls_code", "corplifestage": "life_stage",
        "leverage": "leverage", "levpct": "lev_pct",
        "prof": "profitability", "tang": "tangibility", "tax": "tax",
        "dvnd": "dividend", "interest": "interest", "size": "firm_size",
        "logsize": "log_size", "lnsize": "ln_size", "taxShield": "tax_shield",
        "logtaxShield": "log_tax_shield",
        "pbit": "pbit", "pbt": "pbt", "Intamt": "interest_amt",
        "totalcapital": "total_capital", "reservesandfunds": "reserves_and_funds",
        "borrowings": "borrowings", "debenturesandbonds": "debentures_bonds",
        "totalliabilities": "total_liabilities",
        "ncfo": "ncfo", "ncfi": "ncfi", "ncff": "ncff",
        "netcashflow": "net_cash_flow", "ncfDummy": "ncf_dummy",
        "stinvest": "st_invest", "cashbal": "cash_bal", "bankbal": "bank_bal",
        "cashholdings": "cash_holdings",
        "prof100": "prof100", "tang100": "tang100", "lev1_100": "lev1_100",
        "pbit1": "pbit1", "pbt1": "pbt1", "Intamt1": "intamt1",
        "taxShield1": "tax_shield1", "logtaxShield1": "log_tax_shield1", "logtang": "log_tang",
        "oc": "oc", "ic": "ic", "fc": "fc",
        "GFC": "gfc", "ibc2016": "ibc_2016", "ibc201620": "ibc_2016_20",
        "dcovid20less": "covid_dummy",
        "intRate": "int_rate", "intRateLT": "int_rate_lt",
    }

    fin_df = df[list(fin_cols_map.keys())].rename(columns=fin_cols_map)
    fin_df["year"] = fin_df["year"].astype(int)
    fin_df["company_code"] = fin_df["company_code"].astype(int)
    fin_df["cls_code"] = fin_df["cls_code"].astype(int)
    # Convert numpy/pandas NaN to None for SQLite
    fin_df = fin_df.where(fin_df.notna(), None)
    fin_df.to_sql("financials", conn, if_exists="append", index=False)
    print(f"  financials: {len(fin_df):,} rows")

    # ── 4. Ownership (promoter/non-promoter shareholding) ──
    cur.execute("""
        CREATE TABLE ownership (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code        INTEGER NOT NULL,
            year                INTEGER NOT NULL,
            -- Promoter holdings
            promoter_share          REAL,
            indian_promoters        REAL,
            foreign_promoters       REAL,
            promoters_pledged       REAL,
            -- Non-promoter holdings
            non_promoters           REAL,
            non_promoter_institutions   REAL,
            non_promoter_mutual_funds   REAL,
            non_promoter_banks_fis      REAL,
            non_promoter_fin_institutions REAL,
            non_promoter_insurance      REAL,
            non_promoter_fiis           REAL,
            non_promoter_non_institutions REAL,
            non_promoter_corporate_bodies REAL,
            non_promoter_individuals    REAL,
            total_share             REAL,
            total_shares_pledged    REAL,
            FOREIGN KEY (company_code) REFERENCES companies(company_code)
        )
    """)

    own_cols_map = {
        "companycode": "company_code", "year": "year",
        "pmShare": "promoter_share", "indianpromoters": "indian_promoters",
        "foreignpromoters": "foreign_promoters", "promoterspledged": "promoters_pledged",
        "nonpromoters": "non_promoters",
        "nonpromoterinstitutions": "non_promoter_institutions",
        "nonpromotermutualfundsuti": "non_promoter_mutual_funds",
        "nonpromoterbanksfisinsurancecos": "non_promoter_banks_fis",
        "nonpromoterfinancialinstitutions": "non_promoter_fin_institutions",
        "nonpromoterinsurancecompanies": "non_promoter_insurance",
        "nonpromoterfiis": "non_promoter_fiis",
        "nonpromoternoninstitutions": "non_promoter_non_institutions",
        "nonpromotercorporatebodies": "non_promoter_corporate_bodies",
        "nonpromoterindividuals": "non_promoter_individuals",
        "totalshare": "total_share",
        "totalsharespledged": "total_shares_pledged",
    }

    own_df = df[list(own_cols_map.keys())].rename(columns=own_cols_map)
    own_df["year"] = own_df["year"].astype(int)
    own_df["company_code"] = own_df["company_code"].astype(int)
    own_df = own_df.where(own_df.notna(), None)
    own_df.to_sql("ownership", conn, if_exists="append", index=False)
    print(f"  ownership: {len(own_df):,} rows")

    # ── 5. Market index data ──
    cur.execute("""
        CREATE TABLE market_index (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            year            INTEGER NOT NULL,
            index_code      INTEGER,
            index_name      TEXT,
            index_date      TEXT,
            index_opening   REAL,
            index_closing   REAL,
            index_high      REAL,
            index_low       REAL,
            index_market_cap    REAL,
            index_free_float_cap REAL,
            daily_returns   REAL,
            excess_returns  REAL,
            index_pe        REAL,
            index_pb        REAL,
            index_yield     REAL,
            index_volume    REAL,
            num_companies   INTEGER,
            index_beta      REAL,
            index_alpha     REAL,
            index_r_square  REAL,
            return_index_closing REAL
        )
    """)

    idx_cols = ["year", "indexcode", "indexname", "indexdate", "indexopening",
                "indexclosing", "indexhigh", "indexlow", "indexmarketcap",
                "indexfreefloatmarketcap", "dailyindexreturns", "excessreturnsovercospi",
                "indexpe", "indexpb", "indexyield", "indextradingvolume",
                "numberofcompaniesinindex", "indexbeta", "indexalpha", "indexrsquare",
                "returnIndexClosing"]
    idx_rename = {
        "indexcode": "index_code", "indexname": "index_name", "indexdate": "index_date",
        "indexopening": "index_opening", "indexclosing": "index_closing",
        "indexhigh": "index_high", "indexlow": "index_low",
        "indexmarketcap": "index_market_cap", "indexfreefloatmarketcap": "index_free_float_cap",
        "dailyindexreturns": "daily_returns", "excessreturnsovercospi": "excess_returns",
        "indexpe": "index_pe", "indexpb": "index_pb", "indexyield": "index_yield",
        "indextradingvolume": "index_volume", "numberofcompaniesinindex": "num_companies",
        "indexbeta": "index_beta", "indexalpha": "index_alpha", "indexrsquare": "index_r_square",
        "returnIndexClosing": "return_index_closing",
    }
    idx_df = df[idx_cols].rename(columns=idx_rename).drop_duplicates()
    idx_df["year"] = idx_df["year"].astype(int)
    idx_df = idx_df.where(idx_df.notna(), None)
    idx_df.to_sql("market_index", conn, if_exists="append", index=False)
    print(f"  market_index: {len(idx_df)} rows")

    # ── 6. Create indexes for fast queries ──
    indexes = [
        "CREATE INDEX idx_fin_company ON financials(company_code)",
        "CREATE INDEX idx_fin_year ON financials(year)",
        "CREATE INDEX idx_fin_cls ON financials(cls_code)",
        "CREATE INDEX idx_fin_company_year ON financials(company_code, year)",
        "CREATE INDEX idx_own_company_year ON ownership(company_code, year)",
        "CREATE INDEX idx_mkt_year ON market_index(year)",
    ]
    for idx in indexes:
        cur.execute(idx)
    print("  indexes created")

    # ── 7. Create useful views ──
    cur.execute("""
        CREATE VIEW v_company_financials AS
        SELECT
            f.company_code,
            c.company_name,
            c.nse_symbol,
            c.industry_group,
            c.inc_year,
            f.year,
            f.age_group,
            f.size_decile,
            f.life_stage,
            f.leverage,
            f.profitability,
            f.tangibility,
            f.tax,
            f.dividend,
            f.firm_size,
            f.tax_shield,
            f.borrowings,
            f.total_liabilities,
            f.cash_holdings,
            f.gfc,
            f.ibc_2016,
            f.covid_dummy
        FROM financials f
        JOIN companies c ON f.company_code = c.company_code
    """)

    cur.execute("""
        CREATE VIEW v_life_stage_summary AS
        SELECT
            f.life_stage,
            f.year,
            COUNT(*) AS num_firms,
            AVG(f.leverage) AS avg_leverage,
            AVG(f.profitability) AS avg_profitability,
            AVG(f.tangibility) AS avg_tangibility,
            AVG(f.firm_size) AS avg_size,
            AVG(f.tax_shield) AS avg_tax_shield,
            AVG(f.cash_holdings) AS avg_cash_holdings
        FROM financials f
        GROUP BY f.life_stage, f.year
    """)

    cur.execute("""
        CREATE VIEW v_industry_summary AS
        SELECT
            c.industry_group,
            f.year,
            COUNT(*) AS num_firms,
            AVG(f.leverage) AS avg_leverage,
            AVG(f.profitability) AS avg_profitability,
            AVG(f.borrowings) AS avg_borrowings
        FROM financials f
        JOIN companies c ON f.company_code = c.company_code
        GROUP BY c.industry_group, f.year
    """)
    print("  views created")

    conn.commit()
    conn.close()
    db_size = os.path.getsize(DB_PATH)
    print(f"\nDatabase created: {DB_PATH}")
    print(f"Size: {db_size / 1024 / 1024:.1f} MB")


def verify_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    print("\n=== Verification ===")
    for table in ["companies", "life_stages", "financials", "ownership", "market_index"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table}: {cur.fetchone()[0]:,} rows")

    print("\n=== Sample: Life stage leverage summary ===")
    cur.execute("""
        SELECT life_stage, COUNT(*) as n,
               ROUND(AVG(avg_leverage),2) as mean_lev,
               ROUND(MIN(avg_leverage),2) as min_lev,
               ROUND(MAX(avg_leverage),2) as max_lev
        FROM v_life_stage_summary
        GROUP BY life_stage
        ORDER BY mean_lev DESC
    """)
    print(f"  {'Stage':<15} {'N':>5} {'Mean Lev':>10} {'Min':>8} {'Max':>8}")
    for row in cur.fetchall():
        print(f"  {row[0]:<15} {row[1]:>5} {row[2]:>10} {row[3]:>8} {row[4]:>8}")

    conn.close()


if __name__ == "__main__":
    df = load_data()
    create_database(df)
    verify_database()
