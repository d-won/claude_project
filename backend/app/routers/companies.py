"""API endpoints for company search and financial data."""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.schemas import Market, FinancialDataRequest
from ..services.financial_data import (
    search_companies, get_company_info, get_financial_statements, compute_metrics
)
from ..services.demo_data import DEMO_COMPANIES, build_demo_statements

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    market: Optional[Market] = Query(None, description="Filter by market"),
):
    """Search for companies across global markets."""
    try:
        results = search_companies(q, market)
        if results:
            return {"results": results}
    except Exception as e:
        logger.warning(f"Yahoo Finance search failed: {e}")

    # Fallback to demo data
    q_upper = q.upper()
    demo_results = [
        c for ticker, c in DEMO_COMPANIES.items()
        if q_upper in ticker.upper() or q_upper in c.name.upper()
    ]
    if market:
        demo_results = [c for c in demo_results if c.market == market]
    return {"results": demo_results}


@router.get("/{ticker}/info")
async def company_info(ticker: str):
    """Get company information."""
    try:
        info = get_company_info(ticker)
        return info
    except Exception:
        if ticker in DEMO_COMPANIES:
            return DEMO_COMPANIES[ticker]
        raise HTTPException(status_code=404, detail=f"Company not found: {ticker}")


@router.get("/{ticker}/financials")
async def financials(
    ticker: str,
    years: int = Query(default=10, ge=7, le=15),
):
    """Get financial statements for a company."""
    statements = None
    info = None

    # Try live data first
    try:
        statements = get_financial_statements(ticker, years)
        if statements:
            info = get_company_info(ticker)
    except Exception as e:
        logger.warning(f"Yahoo Finance data failed for {ticker}: {e}")

    # Fallback to demo data
    if not statements:
        statements = build_demo_statements(ticker, years)
        info = DEMO_COMPANIES.get(ticker)

    if not statements:
        raise HTTPException(status_code=404, detail="No financial data found")

    metrics = compute_metrics(statements)
    return {
        "company": info,
        "statements": statements,
        "metrics": metrics,
    }
