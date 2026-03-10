"""Service for fetching financial data from Yahoo Finance for global markets."""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from cachetools import TTLCache
from typing import Optional

from ..models.schemas import (
    CompanyInfo, Market, FinancialStatement, FinancialMetrics
)

# Cache: 1000 items, 1 hour TTL
_ticker_cache = TTLCache(maxsize=1000, ttl=3600)

# Market suffix mapping
MARKET_SUFFIXES = {
    Market.KR: ".KS",    # KOSPI
    Market.JP: ".T",     # Tokyo
    Market.EU: "",       # varies by exchange
    Market.US: "",
}

# European exchange suffixes
EU_EXCHANGES = {
    "XETRA": ".DE",
    "LSE": ".L",
    "EURONEXT_PARIS": ".PA",
    "EURONEXT_AMSTERDAM": ".AS",
    "SIX": ".SW",
    "BME": ".MC",
    "BORSA_ITALIANA": ".MI",
}


def _safe_float(value) -> Optional[float]:
    """Safely convert a value to float, returning None for invalid values."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _get_ticker(symbol: str) -> yf.Ticker:
    """Get a cached yfinance Ticker object."""
    if symbol not in _ticker_cache:
        _ticker_cache[symbol] = yf.Ticker(symbol)
    return _ticker_cache[symbol]


def detect_market(ticker_symbol: str) -> Market:
    """Detect the market from a ticker symbol."""
    if ticker_symbol.endswith(".KS") or ticker_symbol.endswith(".KQ"):
        return Market.KR
    elif ticker_symbol.endswith(".T"):
        return Market.JP
    elif any(ticker_symbol.endswith(s) for s in EU_EXCHANGES.values() if s):
        return Market.EU
    return Market.US


def search_companies(query: str, market: Optional[Market] = None) -> list[CompanyInfo]:
    """Search for companies across global markets."""
    results = []

    # Construct search variants based on market
    search_tickers = [query.upper()]

    if market == Market.KR or market is None:
        # Korean stocks: try adding .KS suffix
        if not query.endswith((".KS", ".KQ")):
            search_tickers.append(f"{query}.KS")
            search_tickers.append(f"{query}.KQ")

    if market == Market.JP or market is None:
        if not query.endswith(".T"):
            search_tickers.append(f"{query}.T")

    if market == Market.EU or market is None:
        for suffix in EU_EXCHANGES.values():
            if suffix and not query.endswith(suffix):
                search_tickers.append(f"{query}{suffix}")

    for ticker_str in search_tickers:
        try:
            ticker = _get_ticker(ticker_str)
            info = ticker.info
            if info and info.get("shortName"):
                detected_market = detect_market(ticker_str)
                if market is not None and detected_market != market:
                    continue
                results.append(CompanyInfo(
                    ticker=ticker_str,
                    name=info.get("shortName", ""),
                    market=detected_market,
                    sector=info.get("sector", "N/A"),
                    industry=info.get("industry", "N/A"),
                    currency=info.get("currency", "USD"),
                    exchange=info.get("exchange", "N/A"),
                ))
        except Exception:
            continue

    # Also try yfinance search
    try:
        search_results = yf.Search(query)
        if hasattr(search_results, "quotes"):
            for quote in search_results.quotes[:10]:
                symbol = quote.get("symbol", "")
                if symbol and symbol not in [r.ticker for r in results]:
                    detected = detect_market(symbol)
                    if market is not None and detected != market:
                        continue
                    results.append(CompanyInfo(
                        ticker=symbol,
                        name=quote.get("shortname") or quote.get("longname", ""),
                        market=detected,
                        sector=quote.get("sector", "N/A"),
                        industry=quote.get("industry", "N/A"),
                        currency=quote.get("currency", "USD"),
                        exchange=quote.get("exchange", "N/A"),
                    ))
    except Exception:
        pass

    return results[:20]


def get_company_info(ticker_symbol: str) -> CompanyInfo:
    """Get detailed company information."""
    ticker = _get_ticker(ticker_symbol)
    info = ticker.info
    return CompanyInfo(
        ticker=ticker_symbol,
        name=info.get("shortName") or info.get("longName", "Unknown"),
        market=detect_market(ticker_symbol),
        sector=info.get("sector", "N/A"),
        industry=info.get("industry", "N/A"),
        currency=info.get("currency", "USD"),
        exchange=info.get("exchange", "N/A"),
    )


def get_financial_statements(ticker_symbol: str, years: int = 10) -> list[FinancialStatement]:
    """Fetch financial statements for the specified number of years."""
    ticker = _get_ticker(ticker_symbol)
    info = ticker.info
    currency = info.get("currency", "USD")

    # Fetch all financial data
    income_stmt = ticker.income_stmt
    balance_sheet = ticker.balance_sheet
    cashflow = ticker.cashflow

    # Also fetch quarterly for more recent data
    income_q = ticker.quarterly_income_stmt
    balance_q = ticker.quarterly_balance_sheet
    cashflow_q = ticker.quarterly_cashflow

    statements = []
    current_year = datetime.now().year

    # Process annual data
    if income_stmt is not None and not income_stmt.empty:
        for col in income_stmt.columns:
            year = col.year if hasattr(col, "year") else int(str(col)[:4])
            if year < current_year - years:
                continue

            stmt = _build_statement(
                year, currency, income_stmt, balance_sheet, cashflow, col
            )
            statements.append(stmt)

    # Sort by year
    statements.sort(key=lambda s: s.year)

    # Trim to requested years
    if len(statements) > years:
        statements = statements[-years:]

    return statements


def _build_statement(
    year: int,
    currency: str,
    income_stmt: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    col,
) -> FinancialStatement:
    """Build a FinancialStatement from DataFrames for a given column."""

    def get_val(df: Optional[pd.DataFrame], keys: list[str]) -> Optional[float]:
        if df is None or df.empty or col not in df.columns:
            return None
        for key in keys:
            if key in df.index:
                return _safe_float(df.loc[key, col])
        return None

    # 손익계산서
    revenue = get_val(income_stmt, ["Total Revenue", "Revenue"])
    cost_of_revenue = get_val(income_stmt, ["Cost Of Revenue", "Cost of Revenue"])
    gross_profit = get_val(income_stmt, ["Gross Profit"])
    sga = get_val(income_stmt, ["Selling General And Administration", "Selling General And Administrative"])
    rnd = get_val(income_stmt, ["Research And Development", "Research Development"])
    operating_income = get_val(income_stmt, ["Operating Income", "EBIT"])
    other_income = get_val(income_stmt, ["Other Non Operating Income Expenses",
                                          "Other Income Expense", "Special Income Charges"])
    pretax_income = get_val(income_stmt, ["Pretax Income", "Income Before Tax"])
    net_income = get_val(income_stmt, ["Net Income", "Net Income Common Stockholders"])
    ebitda = get_val(income_stmt, ["EBITDA", "Normalized EBITDA"])
    depreciation = get_val(income_stmt, ["Depreciation And Amortization In Income Statement",
                                         "Reconciled Depreciation"])
    interest_expense = get_val(income_stmt, ["Interest Expense", "Net Interest Income"])
    tax_expense = get_val(income_stmt, ["Tax Provision", "Income Tax Expense"])
    eps = get_val(income_stmt, ["Basic EPS", "Diluted EPS"])

    # 재무상태표 - 자산
    total_assets = get_val(balance_sheet, ["Total Assets"])
    current_assets = get_val(balance_sheet, ["Current Assets"])
    cash = get_val(balance_sheet, ["Cash And Cash Equivalents"])
    short_term_inv = get_val(balance_sheet, ["Other Short Term Investments",
                                              "Cash Cash Equivalents And Short Term Investments"])
    if cash is None:
        cash = short_term_inv
        short_term_inv = None
    accounts_receivable = get_val(balance_sheet, ["Accounts Receivable", "Receivables", "Net Receivables"])
    inventory = get_val(balance_sheet, ["Inventory", "Raw Materials"])
    non_current_assets = get_val(balance_sheet, ["Total Non Current Assets"])
    ppe_net = get_val(balance_sheet, ["Net PPE", "Gross PPE", "Properties"])
    goodwill_intangibles = get_val(balance_sheet, ["Goodwill And Other Intangible Assets",
                                                    "Goodwill", "Other Intangible Assets"])
    long_term_inv = get_val(balance_sheet, ["Long Term Investments", "Investments And Advances",
                                             "Other Non Current Assets"])

    # 재무상태표 - 부채
    total_liabilities = get_val(balance_sheet, ["Total Liabilities Net Minority Interest",
                                                 "Total Liabilities"])
    current_liabilities = get_val(balance_sheet, ["Current Liabilities"])
    accounts_payable = get_val(balance_sheet, ["Accounts Payable", "Payables And Accrued Expenses"])
    short_term_debt_val = get_val(balance_sheet, ["Current Debt", "Current Debt And Capital Lease Obligation",
                                                   "Current Capital Lease Obligation"])
    non_current_liabilities = get_val(balance_sheet, ["Total Non Current Liabilities Net Minority Interest",
                                                       "Total Non Current Liabilities"])
    long_term_debt_val = get_val(balance_sheet, ["Long Term Debt", "Long Term Debt And Capital Lease Obligation"])
    total_debt = get_val(balance_sheet, ["Total Debt"])
    if total_debt is None and long_term_debt_val is not None:
        total_debt = long_term_debt_val + (short_term_debt_val or 0)

    # 재무상태표 - 자본
    total_equity = get_val(balance_sheet, ["Total Equity Gross Minority Interest",
                                            "Stockholders Equity", "Total Stockholder Equity"])
    retained_earnings = get_val(balance_sheet, ["Retained Earnings"])
    shares = get_val(balance_sheet, ["Share Issued", "Ordinary Shares Number"])

    # 현금흐름표
    ocf = get_val(cashflow, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
    dep_cf = get_val(cashflow, ["Depreciation And Amortization", "Depreciation Amortization Depletion"])
    wc_change = get_val(cashflow, ["Change In Working Capital", "Changes In Working Capital"])
    capex = get_val(cashflow, ["Capital Expenditure", "Purchase Of PPE"])
    inv_cf = get_val(cashflow, ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"])
    purchase_inv = get_val(cashflow, ["Purchase Of Investment", "Net Investment Purchase And Sale"])
    sale_inv = get_val(cashflow, ["Sale Of Investment"])
    fin_cf = get_val(cashflow, ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"])
    debt_issue = get_val(cashflow, ["Issuance Of Debt", "Long Term Debt Issuance"])
    debt_repay = get_val(cashflow, ["Repayment Of Debt", "Long Term Debt Payments"])
    share_buyback = get_val(cashflow, ["Net Common Stock Issuance", "Common Stock Issuance",
                                        "Repurchase Of Capital Stock"])
    dividends = get_val(cashflow, ["Cash Dividends Paid", "Common Stock Dividend Paid"])

    fcf = None
    if ocf is not None and capex is not None:
        fcf = ocf + capex  # capex is typically negative

    return FinancialStatement(
        year=year,
        revenue=revenue,
        cost_of_revenue=cost_of_revenue,
        gross_profit=gross_profit,
        selling_general_admin=sga,
        research_development=rnd,
        operating_income=operating_income,
        other_income_expense=other_income,
        pretax_income=pretax_income,
        net_income=net_income,
        ebitda=ebitda,
        depreciation=depreciation,
        interest_expense=interest_expense,
        tax_expense=tax_expense,
        eps=eps,
        total_assets=total_assets,
        current_assets=current_assets,
        cash_and_equivalents=cash,
        short_term_investments=short_term_inv,
        accounts_receivable=accounts_receivable,
        inventory=inventory,
        non_current_assets=non_current_assets,
        ppe_net=ppe_net,
        goodwill_intangibles=goodwill_intangibles,
        long_term_investments=long_term_inv,
        total_liabilities=total_liabilities,
        current_liabilities=current_liabilities,
        accounts_payable=accounts_payable,
        short_term_debt=short_term_debt_val,
        non_current_liabilities=non_current_liabilities,
        long_term_debt=long_term_debt_val,
        total_debt=total_debt,
        total_equity=total_equity,
        retained_earnings=retained_earnings,
        shares_outstanding=shares,
        operating_cash_flow=ocf,
        depreciation_cf=dep_cf,
        change_in_working_capital=wc_change,
        capital_expenditure=capex,
        investing_cash_flow=inv_cf,
        purchase_of_investments=purchase_inv,
        sale_of_investments=sale_inv,
        financing_cash_flow=fin_cf,
        debt_issuance=debt_issue,
        debt_repayment=debt_repay,
        share_buyback_issuance=share_buyback,
        dividends_paid=dividends,
        free_cash_flow=fcf,
        currency=currency,
    )


def compute_metrics(statements: list[FinancialStatement]) -> list[FinancialMetrics]:
    """Compute financial ratios and metrics from statements."""
    metrics_list = []

    for i, stmt in enumerate(statements):
        rev = stmt.revenue
        gross = stmt.gross_profit
        op_inc = stmt.operating_income
        ni = stmt.net_income
        ta = stmt.total_assets
        te = stmt.total_equity
        tl = stmt.total_liabilities
        td = stmt.total_debt
        ie = stmt.interest_expense
        fcf = stmt.free_cash_flow
        ebitda = stmt.ebitda

        gross_margin = (gross / rev) if (rev and gross) else None
        operating_margin = (op_inc / rev) if (rev and op_inc) else None
        net_margin = (ni / rev) if (rev and ni) else None
        roe = (ni / te) if (te and ni and te != 0) else None
        roa = (ni / ta) if (ta and ni and ta != 0) else None

        # ROIC = NOPAT / Invested Capital
        roic = None
        if op_inc and stmt.tax_expense and rev and ta and tl:
            effective_tax = stmt.tax_expense / (op_inc if op_inc != 0 else 1)
            if effective_tax < 0:
                effective_tax = 0.25  # default
            nopat = op_inc * (1 - effective_tax)
            invested_capital = ta - tl + (td or 0)
            if invested_capital > 0:
                roic = nopat / invested_capital

        d_to_e = (td / te) if (td and te and te != 0) else None

        current_ratio = None
        if stmt.current_assets and stmt.current_liabilities and stmt.current_liabilities != 0:
            current_ratio = stmt.current_assets / stmt.current_liabilities

        interest_coverage = None
        if ebitda and ie and ie != 0:
            interest_coverage = abs(ebitda / ie)

        asset_turnover = (rev / ta) if (rev and ta and ta != 0) else None

        rev_growth = None
        earn_growth = None
        if i > 0:
            prev = statements[i - 1]
            if prev.revenue and rev and prev.revenue != 0:
                rev_growth = (rev - prev.revenue) / abs(prev.revenue)
            if prev.net_income and ni and prev.net_income != 0:
                earn_growth = (ni - prev.net_income) / abs(prev.net_income)

        fcf_margin = (fcf / rev) if (rev and fcf) else None

        metrics_list.append(FinancialMetrics(
            year=stmt.year,
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            roe=roe,
            roa=roa,
            roic=roic,
            debt_to_equity=d_to_e,
            current_ratio=current_ratio,
            interest_coverage=interest_coverage,
            asset_turnover=asset_turnover,
            revenue_growth=rev_growth,
            earnings_growth=earn_growth,
            fcf_margin=fcf_margin,
        ))

    return metrics_list
