"""API endpoints for company search and financial data."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.schemas import Market, FinancialDataRequest
from ..services.financial_data import (
    search_companies, get_company_info, get_financial_statements, compute_metrics
)

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    market: Optional[Market] = Query(None, description="Filter by market"),
):
    """Search for companies across global markets."""
    try:
        results = search_companies(q, market)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/info")
async def company_info(ticker: str):
    """Get company information."""
    try:
        info = get_company_info(ticker)
        return info
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Company not found: {e}")


@router.get("/{ticker}/financials")
async def financials(
    ticker: str,
    years: int = Query(default=10, ge=7, le=15),
):
    """Get financial statements for a company."""
    try:
        statements = get_financial_statements(ticker, years)
        if not statements:
            raise HTTPException(status_code=404, detail="No financial data found")
        metrics = compute_metrics(statements)
        info = get_company_info(ticker)
        return {
            "company": info,
            "statements": statements,
            "metrics": metrics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
