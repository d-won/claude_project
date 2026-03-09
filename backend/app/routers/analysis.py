"""API endpoints for SWOT analysis and DCF valuation."""

from fastapi import APIRouter, HTTPException

from ..models.schemas import SWOTRequest, DCFRequest
from ..services.financial_data import (
    get_company_info, get_financial_statements, compute_metrics
)
from ..services.swot_analysis import generate_swot
from ..services.dcf_valuation import perform_dcf

import yfinance as yf

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/swot")
async def swot_analysis(req: SWOTRequest):
    """Generate SWOT analysis for a company."""
    try:
        info = get_company_info(req.ticker)
        statements = get_financial_statements(req.ticker, req.years)
        if not statements:
            raise HTTPException(status_code=404, detail="No financial data found")
        metrics = compute_metrics(statements)

        swot = generate_swot(
            company_name=info.name,
            sector=info.sector,
            industry=info.industry,
            statements=statements,
            metrics=metrics,
        )

        return {
            "company": info,
            "swot": swot,
            "data_years": len(statements),
            "period": f"{statements[0].year}-{statements[-1].year}" if statements else "N/A",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dcf")
async def dcf_valuation(req: DCFRequest):
    """Perform DCF valuation for a company."""
    try:
        info = get_company_info(req.ticker)
        statements = get_financial_statements(req.ticker, req.years)
        if not statements:
            raise HTTPException(status_code=404, detail="No financial data found")
        metrics = compute_metrics(statements)

        # Get market data
        ticker = yf.Ticker(req.ticker)
        yf_info = ticker.info
        current_price = yf_info.get("currentPrice") or yf_info.get("regularMarketPrice", 0)
        beta = yf_info.get("beta", 1.0) or 1.0
        market_cap = yf_info.get("marketCap", 0) or 0

        dcf = perform_dcf(
            company_name=info.name,
            sector=info.sector,
            industry=info.industry,
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
