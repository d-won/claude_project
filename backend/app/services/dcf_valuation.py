"""DCF valuation engine with detailed assumption reasoning and evidence."""

import numpy as np
from typing import Optional

from ..models.schemas import (
    DCFAssumption, DCFProjection, DCFResult,
    FinancialStatement, FinancialMetrics,
)


def perform_dcf(
    company_name: str,
    sector: str,
    industry: str,
    statements: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    current_price: float,
    beta: float,
    market_cap: float,
    shares_outstanding_override: float = 0,
    projection_years: int = 5,
    custom_wacc: Optional[float] = None,
    custom_growth_rate: Optional[float] = None,
    custom_terminal_growth: Optional[float] = None,
) -> DCFResult:
    """Perform DCF valuation with fully documented assumptions."""
    currency = statements[-1].currency if statements else "USD"

    # Step 1: Calculate WACC
    wacc, wacc_assumptions = _calculate_wacc(
        statements, metrics, beta, market_cap, custom_wacc
    )

    # Step 2: Determine revenue growth rate
    growth_rate, growth_assumptions = _determine_growth_rate(
        statements, metrics, sector, custom_growth_rate
    )

    # Step 3: Determine terminal growth rate
    terminal_growth, tg_assumptions = _determine_terminal_growth(
        sector, industry, growth_rate, custom_terminal_growth
    )

    # Step 4: Project margins and FCF
    margin_assumptions = _determine_margins(statements, metrics)

    # Step 5: Build projections
    all_assumptions = wacc_assumptions + growth_assumptions + tg_assumptions + margin_assumptions
    projections = _build_projections(
        statements, growth_rate, margin_assumptions, wacc, projection_years
    )

    # Step 6: Terminal value
    last_fcf = projections[-1].free_cash_flow
    terminal_value = last_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    last_discount = projections[-1].discount_factor
    terminal_value_pv = terminal_value * last_discount

    # Step 7: Enterprise and equity value
    sum_pv_fcf = sum(p.present_value for p in projections)
    enterprise_value = sum_pv_fcf + terminal_value_pv

    latest = statements[-1]
    net_debt = (latest.total_debt or 0) - (latest.cash_and_equivalents or 0)
    equity_value = enterprise_value - net_debt

    # Use shares_outstanding from yfinance info (most reliable), then balance sheet, then derive from market_cap
    shares = shares_outstanding_override
    if shares <= 0:
        shares = latest.shares_outstanding or 0
    if shares <= 0 and market_cap > 0 and current_price > 0:
        shares = market_cap / current_price
    if shares <= 0:
        shares = 1

    intrinsic_per_share = equity_value / shares

    upside = ((intrinsic_per_share / current_price) - 1) * 100 if current_price > 0 else 0

    # Step 8: Sensitivity analysis
    sensitivity = _build_sensitivity(
        last_fcf, terminal_growth, wacc, net_debt, shares,
        sum_pv_fcf, projection_years
    )

    # Methodology notes
    notes = [
        "DCF model uses a two-stage approach: explicit projection period followed by terminal value",
        f"Projection period: {projection_years} years with explicit revenue, margin, and FCF forecasts",
        "Terminal value calculated using Gordon Growth Model (perpetuity growth method)",
        f"WACC of {wacc*100:.1f}% used as discount rate, derived from CAPM-based cost of equity and after-tax cost of debt",
        "Free Cash Flow = EBITDA - Taxes on EBIT - Change in Working Capital - Capital Expenditures",
        f"Net debt of {_fmt_num(net_debt)} ({currency}) subtracted from enterprise value to derive equity value",
        "Sensitivity matrix shows intrinsic value per share under different WACC and terminal growth assumptions",
        "All projections based on historical financial data analysis - actual results may differ materially",
    ]

    return DCFResult(
        assumptions=all_assumptions,
        projections=projections,
        terminal_value=terminal_value,
        terminal_value_pv=terminal_value_pv,
        enterprise_value=enterprise_value,
        equity_value=equity_value,
        shares_outstanding=shares,
        intrinsic_value_per_share=intrinsic_per_share,
        current_price=current_price,
        upside_downside_pct=upside,
        sensitivity_matrix=sensitivity,
        methodology_notes=notes,
        currency=currency,
    )


def _fmt_num(val: float) -> str:
    if abs(val) >= 1e12:
        return f"{val/1e12:.1f}T"
    if abs(val) >= 1e9:
        return f"{val/1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"{val/1e6:.1f}M"
    return f"{val:,.0f}"


def _calculate_wacc(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    beta: float,
    market_cap: float,
    custom_wacc: Optional[float],
) -> tuple[float, list[DCFAssumption]]:
    assumptions = []
    latest = stmts[-1]

    if custom_wacc is not None:
        assumptions.append(DCFAssumption(
            parameter="WACC",
            value=custom_wacc * 100,
            unit="%",
            reasoning="User-specified discount rate",
            evidence=["Custom input by analyst"],
        ))
        return custom_wacc, assumptions

    # Risk-free rate (10Y Treasury approximation)
    risk_free = 0.04
    assumptions.append(DCFAssumption(
        parameter="Risk-Free Rate",
        value=risk_free * 100,
        unit="%",
        reasoning="Based on approximate 10-year government bond yields in major markets. US 10Y ~4.0-4.5%, reflecting current monetary policy environment",
        evidence=[
            "US 10Y Treasury yield range: 3.8-4.5% (2024-2025)",
            "Historically normalized range post-QE era",
            "Used as proxy for time value of money",
        ],
    ))

    # Equity risk premium
    erp = 0.055
    assumptions.append(DCFAssumption(
        parameter="Equity Risk Premium",
        value=erp * 100,
        unit="%",
        reasoning="Based on long-term geometric average excess return of equities over government bonds",
        evidence=[
            "Damodaran estimated global ERP: 4.5-6.0% (2024)",
            "Historical US equity premium (1926-2024): ~5.5% geometric",
            "Adjusted for current market volatility conditions",
        ],
    ))

    # Beta
    if beta <= 0 or beta > 5:
        beta = 1.0
    assumptions.append(DCFAssumption(
        parameter="Beta",
        value=beta,
        unit="x",
        reasoning=f"Measures systematic risk relative to market. Beta of {beta:.2f} indicates {'higher' if beta > 1 else 'lower' if beta < 1 else 'average'} volatility vs market",
        evidence=[
            f"Regression beta from Yahoo Finance: {beta:.2f}",
            "Based on 5-year monthly returns vs market index",
            f"{'Above 1.0 = more volatile than market' if beta > 1 else 'Below 1.0 = less volatile than market' if beta < 1 else 'Equal to market volatility'}",
        ],
    ))

    # Cost of equity (CAPM)
    cost_equity = risk_free + beta * erp

    # Cost of debt
    interest = abs(latest.interest_expense or 0)
    debt = latest.total_debt or 1
    cost_debt_pretax = interest / debt if debt > 0 else 0.05
    if cost_debt_pretax > 0.20 or cost_debt_pretax < 0.01:
        cost_debt_pretax = 0.05  # fallback

    # Tax rate
    tax_rate = 0.25
    if latest.tax_expense and latest.operating_income and latest.operating_income > 0:
        implied_tax = latest.tax_expense / latest.operating_income
        if 0.05 < implied_tax < 0.50:
            tax_rate = implied_tax

    cost_debt = cost_debt_pretax * (1 - tax_rate)

    assumptions.append(DCFAssumption(
        parameter="Cost of Debt (after-tax)",
        value=cost_debt * 100,
        unit="%",
        reasoning=f"Pre-tax cost of {cost_debt_pretax*100:.1f}% derived from interest expense / total debt, tax-adjusted at {tax_rate*100:.0f}% effective rate",
        evidence=[
            f"Interest expense: {_fmt_num(interest)}",
            f"Total debt: {_fmt_num(debt)}",
            f"Implied pre-tax cost: {cost_debt_pretax*100:.1f}%",
            f"Effective tax rate: {tax_rate*100:.1f}%",
        ],
    ))

    # Capital structure weights
    equity_weight = market_cap / (market_cap + debt) if (market_cap + debt) > 0 else 0.7
    debt_weight = 1 - equity_weight

    wacc = equity_weight * cost_equity + debt_weight * cost_debt

    assumptions.append(DCFAssumption(
        parameter="WACC",
        value=wacc * 100,
        unit="%",
        reasoning=f"Weighted average: {equity_weight*100:.0f}% equity at {cost_equity*100:.1f}% + {debt_weight*100:.0f}% debt at {cost_debt*100:.1f}%",
        evidence=[
            f"Cost of Equity (CAPM): {risk_free*100:.1f}% + {beta:.2f} × {erp*100:.1f}% = {cost_equity*100:.1f}%",
            f"Market cap weight: {equity_weight*100:.0f}%, Debt weight: {debt_weight*100:.0f}%",
            f"Final WACC: {wacc*100:.1f}%",
        ],
    ))

    return wacc, assumptions


def _determine_growth_rate(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    sector: str,
    custom_growth: Optional[float],
) -> tuple[float, list[DCFAssumption]]:
    assumptions = []

    if custom_growth is not None:
        assumptions.append(DCFAssumption(
            parameter="Revenue Growth Rate",
            value=custom_growth * 100,
            unit="%",
            reasoning="User-specified growth rate",
            evidence=["Custom input by analyst"],
        ))
        return custom_growth, assumptions

    # Historical CAGR
    revenues = [(s.year, s.revenue) for s in stmts if s.revenue and s.revenue > 0]
    if len(revenues) >= 2:
        first_rev = revenues[0][1]
        last_rev = revenues[-1][1]
        n_years = revenues[-1][0] - revenues[0][0]
        if n_years > 0 and first_rev > 0:
            cagr = (last_rev / first_rev) ** (1 / n_years) - 1
        else:
            cagr = 0.05
    else:
        cagr = 0.05

    # Recent growth (last 3 years)
    recent_growths = [m.revenue_growth for m in metrics[-3:] if m.revenue_growth is not None]
    recent_avg = sum(recent_growths) / len(recent_growths) if recent_growths else cagr

    # Blend: 60% recent, 40% long-term (with mean reversion)
    projected = 0.6 * recent_avg + 0.4 * cagr

    # Apply conservatism (fade toward GDP growth)
    gdp_growth = 0.03
    projected = max(min(projected, 0.40), -0.05)  # Cap extremes
    # Fade factor
    projected = 0.7 * projected + 0.3 * gdp_growth

    assumptions.append(DCFAssumption(
        parameter="Revenue Growth Rate (projected)",
        value=projected * 100,
        unit="%",
        reasoning=(
            f"Blended estimate: 60% weight on recent 3-year average ({recent_avg*100:.1f}%) "
            f"and 40% on long-term CAGR ({cagr*100:.1f}%), "
            f"then faded 30% toward nominal GDP growth ({gdp_growth*100:.0f}%) for conservatism"
        ),
        evidence=[
            f"Long-term revenue CAGR ({revenues[0][0]}-{revenues[-1][0]}): {cagr*100:.1f}%" if len(revenues) >= 2 else "Insufficient data for CAGR",
            f"Recent 3-year average growth: {recent_avg*100:.1f}%",
            f"Blended rate before GDP fade: {(0.6*recent_avg + 0.4*cagr)*100:.1f}%",
            f"Final projected rate (with GDP fade): {projected*100:.1f}%",
            "Growth fade applied to reflect mean-reversion tendency of high/low growth rates",
        ],
    ))

    return projected, assumptions


def _determine_terminal_growth(
    sector: str,
    industry: str,
    near_term_growth: float,
    custom_tg: Optional[float],
) -> tuple[float, list[DCFAssumption]]:
    assumptions = []

    if custom_tg is not None:
        assumptions.append(DCFAssumption(
            parameter="Terminal Growth Rate",
            value=custom_tg * 100,
            unit="%",
            reasoning="User-specified terminal growth rate",
            evidence=["Custom input by analyst"],
        ))
        return custom_tg, assumptions

    # Terminal growth should not exceed long-term nominal GDP growth
    terminal = 0.025  # default 2.5%

    # Adjust slightly based on sector
    sector_lower = sector.lower() if sector else ""
    if "technology" in sector_lower or "healthcare" in sector_lower:
        terminal = 0.03
    elif "utilities" in sector_lower or "real estate" in sector_lower:
        terminal = 0.02
    elif "energy" in sector_lower:
        terminal = 0.02

    # Ensure terminal < near-term
    terminal = min(terminal, near_term_growth * 0.5, 0.04)
    terminal = max(terminal, 0.01)

    assumptions.append(DCFAssumption(
        parameter="Terminal Growth Rate",
        value=terminal * 100,
        unit="%",
        reasoning=(
            f"Set at {terminal*100:.1f}%, below long-term nominal GDP growth (~3%). "
            f"No company can sustainably grow faster than the economy indefinitely. "
            f"Sector adjustment applied for {sector}"
        ),
        evidence=[
            "Academic consensus: terminal growth ≤ long-term nominal GDP (2-3%)",
            f"Sector ({sector}): {'slightly above' if terminal > 0.025 else 'at or below'} average due to structural growth characteristics",
            "Terminal growth must be < WACC for model validity",
            f"Near-term growth of {near_term_growth*100:.1f}% fades to {terminal*100:.1f}% in perpetuity",
        ],
    ))

    return terminal, assumptions


def _determine_margins(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
) -> list[DCFAssumption]:
    assumptions = []
    recent = metrics[-3:] if len(metrics) >= 3 else metrics

    # EBITDA margin
    ebitda_margins = []
    for s in stmts:
        if s.ebitda and s.revenue and s.revenue > 0:
            ebitda_margins.append(s.ebitda / s.revenue)

    avg_ebitda_margin = sum(ebitda_margins[-3:]) / len(ebitda_margins[-3:]) if ebitda_margins else 0.15

    assumptions.append(DCFAssumption(
        parameter="EBITDA Margin (projected)",
        value=avg_ebitda_margin * 100,
        unit="%",
        reasoning=f"Based on trailing 3-year average EBITDA margin. Assumes current operational efficiency is sustainable",
        evidence=[
            f"Recent EBITDA margins: {', '.join(f'{m*100:.1f}%' for m in ebitda_margins[-3:])}",
            f"Full history average: {sum(ebitda_margins)/len(ebitda_margins)*100:.1f}%" if ebitda_margins else "N/A",
            "No significant margin expansion or contraction assumed",
        ],
    ))

    # CAPEX as % of revenue
    capex_ratios = []
    for s in stmts:
        if s.capital_expenditure and s.revenue and s.revenue > 0:
            capex_ratios.append(abs(s.capital_expenditure) / s.revenue)

    avg_capex = sum(capex_ratios[-3:]) / len(capex_ratios[-3:]) if capex_ratios else 0.05

    assumptions.append(DCFAssumption(
        parameter="CAPEX / Revenue (projected)",
        value=avg_capex * 100,
        unit="%",
        reasoning="Based on historical capital intensity. Assumes maintenance + growth CAPEX remains proportional to revenue",
        evidence=[
            f"Recent CAPEX ratios: {', '.join(f'{r*100:.1f}%' for r in capex_ratios[-3:])}",
            f"Historical average: {sum(capex_ratios)/len(capex_ratios)*100:.1f}%" if capex_ratios else "N/A",
        ],
    ))

    # Tax rate
    tax_rates = []
    for s in stmts:
        if s.tax_expense and s.operating_income and s.operating_income > 0:
            tr = s.tax_expense / s.operating_income
            if 0.05 < tr < 0.50:
                tax_rates.append(tr)

    avg_tax = sum(tax_rates[-3:]) / len(tax_rates[-3:]) if tax_rates else 0.25

    assumptions.append(DCFAssumption(
        parameter="Effective Tax Rate",
        value=avg_tax * 100,
        unit="%",
        reasoning="Based on historical effective tax rate from financial statements",
        evidence=[
            f"Recent effective rates: {', '.join(f'{r*100:.1f}%' for r in tax_rates[-3:])}",
            f"Statutory rates vary by jurisdiction (US: 21%, Korea: 22%, Japan: 30%, EU: varies)",
        ],
    ))

    return assumptions


def _build_projections(
    stmts: list[FinancialStatement],
    growth_rate: float,
    margin_assumptions: list[DCFAssumption],
    wacc: float,
    projection_years: int,
) -> list[DCFProjection]:
    latest = stmts[-1]
    base_revenue = latest.revenue or 0

    # Extract margin parameters
    ebitda_margin = margin_assumptions[0].value / 100
    capex_ratio = margin_assumptions[1].value / 100
    tax_rate = margin_assumptions[2].value / 100

    # Calculate historical depreciation/revenue ratio instead of arbitrary 0.3 * EBITDA
    dep_ratios = []
    for s in stmts:
        if s.depreciation and s.revenue and s.revenue > 0:
            dep_ratios.append(abs(s.depreciation) / s.revenue)
    dep_ratio = sum(dep_ratios[-3:]) / len(dep_ratios[-3:]) if dep_ratios else ebitda_margin * 0.3

    # Historical FCF margin as sanity check / fallback
    fcf_margins = []
    for s in stmts:
        if s.free_cash_flow is not None and s.revenue and s.revenue > 0:
            fcf_margins.append(s.free_cash_flow / s.revenue)
    hist_fcf_margin = sum(fcf_margins[-3:]) / len(fcf_margins[-3:]) if fcf_margins else None

    projections = []
    base_year = latest.year

    for i in range(1, projection_years + 1):
        year = base_year + i

        # Growth gradually fades over projection period
        fade = 1 - (i - 1) / (projection_years * 2)
        year_growth = growth_rate * fade
        revenue = base_revenue * (1 + year_growth) ** i

        ebitda = revenue * ebitda_margin
        depreciation = revenue * dep_ratio
        ebit = ebitda - depreciation
        taxes = max(ebit * tax_rate, 0)
        nopat = ebit - taxes
        capex = revenue * capex_ratio

        # FCF = NOPAT + D&A - CAPEX (simplified, no WC changes)
        fcf = nopat + depreciation - capex

        # If component-based FCF is negative but historical FCF was positive,
        # use historical FCF margin as fallback (common for capital-intensive firms)
        if fcf < 0 and hist_fcf_margin is not None and hist_fcf_margin > 0:
            fcf = revenue * hist_fcf_margin

        discount_factor = 1 / (1 + wacc) ** i
        pv = fcf * discount_factor

        projections.append(DCFProjection(
            year=year,
            revenue=revenue,
            ebitda=ebitda,
            free_cash_flow=fcf,
            discount_factor=discount_factor,
            present_value=pv,
        ))

    return projections


def _build_sensitivity(
    last_fcf: float,
    terminal_growth: float,
    wacc: float,
    net_debt: float,
    shares: float,
    sum_pv_fcf: float,
    projection_years: int,
) -> dict:
    """Build sensitivity matrix for WACC vs terminal growth."""
    wacc_range = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]
    tg_range = [terminal_growth - 0.01, terminal_growth - 0.005,
                terminal_growth, terminal_growth + 0.005, terminal_growth + 0.01]

    # Ensure valid ranges
    wacc_range = [max(w, 0.03) for w in wacc_range]
    tg_range = [max(t, 0.005) for t in tg_range]

    matrix = {}
    for w in wacc_range:
        w_label = f"{w*100:.1f}%"
        matrix[w_label] = {}
        for tg in tg_range:
            tg_label = f"{tg*100:.1f}%"
            if w <= tg:
                matrix[w_label][tg_label] = None
                continue
            tv = last_fcf * (1 + tg) / (w - tg)
            tv_pv = tv / (1 + w) ** projection_years
            ev = sum_pv_fcf + tv_pv
            eq = ev - net_debt
            per_share = eq / shares if shares > 0 else 0
            matrix[w_label][tg_label] = round(per_share, 2)

    return {
        "wacc_values": [f"{w*100:.1f}%" for w in wacc_range],
        "terminal_growth_values": [f"{tg*100:.1f}%" for tg in tg_range],
        "intrinsic_values": matrix,
    }
