"""API endpoints for SWOT analysis and DCF valuation."""

import logging
from fastapi import APIRouter, HTTPException

from ..models.schemas import SWOTRequest, DCFRequest
from ..services.financial_data import (
    get_company_info, get_financial_statements, compute_metrics
)
from ..services.swot_analysis import generate_swot
from ..services.dcf_valuation import perform_dcf
from ..services.demo_data import DEMO_COMPANIES, DEMO_MARKET_INFO, build_demo_statements

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _get_data(ticker: str, years: int):
    """Get financial data, falling back to demo data."""
    info = None
    statements = None

    try:
        import yfinance as yf
        statements = get_financial_statements(ticker, years)
        if statements:
            info = get_company_info(ticker)
    except Exception as e:
        logger.warning(f"Yahoo Finance failed for {ticker}: {e}")

    if not statements:
        statements = build_demo_statements(ticker, years)
        info = DEMO_COMPANIES.get(ticker)

    return info, statements


@router.post("/swot")
async def swot_analysis(req: SWOTRequest):
    """Generate SWOT analysis for a company."""
    info, statements = _get_data(req.ticker, req.years)
    if not statements:
        raise HTTPException(status_code=404, detail="No financial data found")

    metrics = compute_metrics(statements)
    swot = generate_swot(
        company_name=info.name if info else req.ticker,
        sector=info.sector if info else "N/A",
        industry=info.industry if info else "N/A",
        statements=statements,
        metrics=metrics,
    )

    return {
        "company": info,
        "swot": swot,
        "data_years": len(statements),
        "period": f"{statements[0].year}-{statements[-1].year}" if statements else "N/A",
    }


@router.post("/dcf")
async def dcf_valuation(req: DCFRequest):
    """Perform DCF valuation for a company."""
    info, statements = _get_data(req.ticker, req.years)
    if not statements:
        raise HTTPException(status_code=404, detail="No financial data found")

    metrics = compute_metrics(statements)

    # Try live market data, fall back to demo
    current_price = 0
    beta = 1.0
    market_cap = 0

    try:
        import yfinance as yf
        ticker_obj = yf.Ticker(req.ticker)
        yf_info = ticker_obj.info
        current_price = yf_info.get("currentPrice") or yf_info.get("regularMarketPrice", 0)
        beta = yf_info.get("beta", 1.0) or 1.0
        market_cap = yf_info.get("marketCap", 0) or 0
    except Exception as e:
        logger.warning(f"Yahoo Finance market data failed: {e}")
        demo_mkt = DEMO_MARKET_INFO.get(req.ticker, {})
        current_price = demo_mkt.get("price", 100)
        beta = demo_mkt.get("beta", 1.0)
        market_cap = demo_mkt.get("market_cap", 1e9)

    dcf = perform_dcf(
        company_name=info.name if info else req.ticker,
        sector=info.sector if info else "Technology",
        industry=info.industry if info else "N/A",
        statements=statements,
        metrics=metrics,
        current_price=current_price,
        beta=beta,
        market_cap=market_cap,
        projection_years=req.projection_years,
        custom_wacc=req.custom_wacc,
        custom_growth_rate=req.custom_growth_rate,
        custom_terminal_growth=req.custom_terminal_growth,
    )

    return {
        "company": info,
        "dcf": dcf,
        "data_years": len(statements),
        "period": f"{statements[0].year}-{statements[-1].year}" if statements else "N/A",
    }
