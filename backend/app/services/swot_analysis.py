"""SWOT analysis engine based on financial data and metrics."""

from ..models.schemas import (
    SWOTAnalysis, SWOTItem, FinancialStatement, FinancialMetrics
)


def generate_swot(
    company_name: str,
    sector: str,
    industry: str,
    statements: list[FinancialStatement],
    metrics: list[FinancialMetrics],
) -> SWOTAnalysis:
    """Generate SWOT analysis based on financial data."""
    strengths = _analyze_strengths(statements, metrics)
    weaknesses = _analyze_weaknesses(statements, metrics)
    opportunities = _analyze_opportunities(statements, metrics, sector, industry)
    threats = _analyze_threats(statements, metrics, sector, industry)

    summary = _build_summary(company_name, strengths, weaknesses, opportunities, threats)

    return SWOTAnalysis(
        strengths=strengths,
        weaknesses=weaknesses,
        opportunities=opportunities,
        threats=threats,
        summary=summary,
    )


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val * 100:.1f}%"


def _fmt_num(val: float | None) -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1e12:
        return f"{val / 1e12:.1f}T"
    if abs(val) >= 1e9:
        return f"{val / 1e9:.1f}B"
    if abs(val) >= 1e6:
        return f"{val / 1e6:.1f}M"
    return f"{val:,.0f}"


def _recent(items: list, n: int = 3):
    """Get last n items."""
    return items[-n:] if len(items) >= n else items


def _avg(values: list[float | None]) -> float | None:
    valid = [v for v in values if v is not None]
    return sum(valid) / len(valid) if valid else None


def _analyze_strengths(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
) -> list[SWOTItem]:
    strengths = []
    recent_m = _recent(metrics)
    recent_s = _recent(stmts)

    # Revenue growth consistency
    growths = [m.revenue_growth for m in metrics if m.revenue_growth is not None]
    if growths:
        positive_years = sum(1 for g in growths if g > 0)
        avg_growth = _avg(growths)
        if positive_years / len(growths) >= 0.7 and avg_growth and avg_growth > 0.03:
            strengths.append(SWOTItem(
                point="Consistent revenue growth",
                evidence=f"Revenue grew in {positive_years} of {len(growths)} years with average growth of {_fmt_pct(avg_growth)}",
                data_reference=f"Revenue trend: {' → '.join(_fmt_num(s.revenue) for s in stmts[-5:])}",
            ))

    # High profitability margins
    avg_op_margin = _avg([m.operating_margin for m in recent_m])
    if avg_op_margin and avg_op_margin > 0.15:
        strengths.append(SWOTItem(
            point="Strong operating profitability",
            evidence=f"Average operating margin of {_fmt_pct(avg_op_margin)} over recent {len(recent_m)} years indicates strong pricing power and cost management",
            data_reference=f"Operating margins: {', '.join(_fmt_pct(m.operating_margin) for m in recent_m)}",
        ))

    # High gross margins
    avg_gross = _avg([m.gross_margin for m in recent_m])
    if avg_gross and avg_gross > 0.40:
        strengths.append(SWOTItem(
            point="High gross margins indicate competitive moat",
            evidence=f"Average gross margin of {_fmt_pct(avg_gross)} suggests strong brand, IP, or network effects that support premium pricing",
            data_reference=f"Gross margins: {', '.join(_fmt_pct(m.gross_margin) for m in recent_m)}",
        ))

    # Strong ROE
    avg_roe = _avg([m.roe for m in recent_m])
    if avg_roe and avg_roe > 0.15:
        strengths.append(SWOTItem(
            point="Excellent return on equity",
            evidence=f"Average ROE of {_fmt_pct(avg_roe)} demonstrates efficient capital allocation and strong value creation for shareholders",
            data_reference=f"ROE: {', '.join(_fmt_pct(m.roe) for m in recent_m)}",
        ))

    # Strong cash generation
    avg_fcf_margin = _avg([m.fcf_margin for m in recent_m])
    if avg_fcf_margin and avg_fcf_margin > 0.10:
        strengths.append(SWOTItem(
            point="Robust free cash flow generation",
            evidence=f"FCF margin of {_fmt_pct(avg_fcf_margin)} provides financial flexibility for investment, buybacks, and dividends",
            data_reference=f"FCF: {', '.join(_fmt_num(s.free_cash_flow) for s in recent_s)}",
        ))

    # Low leverage
    avg_de = _avg([m.debt_to_equity for m in recent_m])
    if avg_de is not None and avg_de < 0.5:
        strengths.append(SWOTItem(
            point="Conservative balance sheet with low leverage",
            evidence=f"Average D/E ratio of {avg_de:.2f}x provides financial stability and capacity for strategic acquisitions",
            data_reference=f"D/E ratios: {', '.join(f'{m.debt_to_equity:.2f}x' if m.debt_to_equity else 'N/A' for m in recent_m)}",
        ))

    # Strong cash position
    if recent_s and recent_s[-1].cash_and_equivalents and recent_s[-1].total_debt:
        net_cash = recent_s[-1].cash_and_equivalents - recent_s[-1].total_debt
        if net_cash > 0:
            strengths.append(SWOTItem(
                point="Net cash position",
                evidence=f"Cash ({_fmt_num(recent_s[-1].cash_and_equivalents)}) exceeds total debt ({_fmt_num(recent_s[-1].total_debt)}), providing net cash of {_fmt_num(net_cash)}",
                data_reference=f"Net cash: {_fmt_num(net_cash)}",
            ))

    if not strengths:
        strengths.append(SWOTItem(
            point="Established market presence",
            evidence="Company maintains operations across the analysis period, demonstrating business durability",
            data_reference=f"Data available for {len(stmts)} years",
        ))

    return strengths


def _analyze_weaknesses(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
) -> list[SWOTItem]:
    weaknesses = []
    recent_m = _recent(metrics)
    recent_s = _recent(stmts)

    # Declining margins
    if len(metrics) >= 3:
        op_margins = [m.operating_margin for m in metrics if m.operating_margin is not None]
        if len(op_margins) >= 3 and op_margins[-1] < op_margins[0]:
            decline = op_margins[0] - op_margins[-1]
            weaknesses.append(SWOTItem(
                point="Declining operating margins",
                evidence=f"Operating margin declined by {_fmt_pct(decline)} from {_fmt_pct(op_margins[0])} to {_fmt_pct(op_margins[-1])}, suggesting increasing cost pressure or competitive pricing erosion",
                data_reference=f"Margin trend: {' → '.join(_fmt_pct(m) for m in op_margins[-5:])}",
            ))

    # High leverage
    avg_de = _avg([m.debt_to_equity for m in recent_m])
    if avg_de is not None and avg_de > 1.5:
        weaknesses.append(SWOTItem(
            point="High financial leverage",
            evidence=f"D/E ratio of {avg_de:.2f}x increases financial risk and limits strategic flexibility. High interest costs could pressure profitability during downturns",
            data_reference=f"D/E: {', '.join(f'{m.debt_to_equity:.2f}x' if m.debt_to_equity else 'N/A' for m in recent_m)}",
        ))

    # Low interest coverage
    avg_ic = _avg([m.interest_coverage for m in recent_m])
    if avg_ic is not None and avg_ic < 3.0:
        weaknesses.append(SWOTItem(
            point="Weak interest coverage",
            evidence=f"Interest coverage of {avg_ic:.1f}x is below the healthy threshold of 3x, indicating potential difficulty servicing debt",
            data_reference=f"Coverage: {', '.join(f'{m.interest_coverage:.1f}x' if m.interest_coverage else 'N/A' for m in recent_m)}",
        ))

    # Negative or volatile earnings
    net_incomes = [s.net_income for s in stmts if s.net_income is not None]
    if net_incomes:
        neg_years = sum(1 for ni in net_incomes if ni < 0)
        if neg_years > 0:
            weaknesses.append(SWOTItem(
                point="Earnings volatility / losses",
                evidence=f"Company reported net losses in {neg_years} of {len(net_incomes)} years, raising concerns about business model sustainability",
                data_reference=f"Net income: {', '.join(_fmt_num(ni) for ni in net_incomes[-5:])}",
            ))

    # Poor FCF conversion
    recent_fcf = [m.fcf_margin for m in recent_m if m.fcf_margin is not None]
    if recent_fcf and _avg(recent_fcf) is not None:
        avg_fcf = _avg(recent_fcf)
        if avg_fcf is not None and avg_fcf < 0.05:
            weaknesses.append(SWOTItem(
                point="Weak free cash flow conversion",
                evidence=f"FCF margin of {_fmt_pct(avg_fcf)} suggests heavy capital requirements or working capital inefficiency",
                data_reference=f"FCF margins: {', '.join(_fmt_pct(f) for f in recent_fcf)}",
            ))

    # Low ROE
    avg_roe = _avg([m.roe for m in recent_m])
    if avg_roe is not None and 0 < avg_roe < 0.08:
        weaknesses.append(SWOTItem(
            point="Below-average return on equity",
            evidence=f"ROE of {_fmt_pct(avg_roe)} is below the typical cost of equity (~8-10%), indicating the company is not creating sufficient shareholder value",
            data_reference=f"ROE: {', '.join(_fmt_pct(m.roe) for m in recent_m)}",
        ))

    if not weaknesses:
        weaknesses.append(SWOTItem(
            point="Limited data on qualitative weaknesses",
            evidence="Financial data alone does not reveal all weaknesses; further qualitative analysis is recommended",
            data_reference="N/A",
        ))

    return weaknesses


def _analyze_opportunities(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    sector: str,
    industry: str,
) -> list[SWOTItem]:
    opportunities = []
    recent_m = _recent(metrics)
    recent_s = _recent(stmts)

    # Accelerating growth
    growths = [m.revenue_growth for m in metrics[-4:] if m.revenue_growth is not None]
    if len(growths) >= 2 and growths[-1] is not None and growths[-2] is not None:
        if growths[-1] > growths[-2] and growths[-1] > 0:
            opportunities.append(SWOTItem(
                point="Accelerating revenue growth momentum",
                evidence=f"Revenue growth accelerated from {_fmt_pct(growths[-2])} to {_fmt_pct(growths[-1])}, suggesting expanding market share or successful new initiatives",
                data_reference=f"Growth trend: {', '.join(_fmt_pct(g) for g in growths)}",
            ))

    # Improving margins
    op_margins = [m.operating_margin for m in metrics if m.operating_margin is not None]
    if len(op_margins) >= 3 and op_margins[-1] > op_margins[-2] > op_margins[-3]:
        opportunities.append(SWOTItem(
            point="Expanding profitability trajectory",
            evidence="Consecutively improving operating margins suggest operational leverage, scale benefits, or successful cost optimization programs",
            data_reference=f"Recent margins: {', '.join(_fmt_pct(m) for m in op_margins[-3:])}",
        ))

    # Under-leveraged (capacity for M&A)
    avg_de = _avg([m.debt_to_equity for m in recent_m])
    cash = recent_s[-1].cash_and_equivalents if recent_s else None
    if avg_de is not None and avg_de < 0.3 and cash:
        opportunities.append(SWOTItem(
            point="M&A capacity from strong balance sheet",
            evidence=f"Low leverage (D/E: {avg_de:.2f}x) combined with {_fmt_num(cash)} cash provides significant capacity for value-accretive acquisitions",
            data_reference=f"Cash: {_fmt_num(cash)}, D/E: {avg_de:.2f}x",
        ))

    # High CAPEX investment
    if recent_s and recent_s[-1].capital_expenditure and recent_s[-1].revenue:
        capex_ratio = abs(recent_s[-1].capital_expenditure) / recent_s[-1].revenue
        if capex_ratio > 0.08:
            opportunities.append(SWOTItem(
                point="Significant reinvestment for future growth",
                evidence=f"Capital expenditure at {_fmt_pct(capex_ratio)} of revenue indicates substantial investment in future capacity and capabilities",
                data_reference=f"CAPEX: {_fmt_num(abs(recent_s[-1].capital_expenditure))}",
            ))

    # Sector-based opportunities
    opportunities.append(SWOTItem(
        point=f"Industry tailwinds in {industry}",
        evidence=f"As a {sector}/{industry} company, positioned to benefit from secular industry trends and structural growth drivers",
        data_reference=f"Sector: {sector}, Industry: {industry}",
    ))

    return opportunities


def _analyze_threats(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    sector: str,
    industry: str,
) -> list[SWOTItem]:
    threats = []
    recent_m = _recent(metrics)

    # Margin compression
    gross_margins = [m.gross_margin for m in metrics if m.gross_margin is not None]
    if len(gross_margins) >= 3 and gross_margins[-1] < gross_margins[0]:
        threats.append(SWOTItem(
            point="Gross margin erosion signals competitive pressure",
            evidence=f"Gross margin declined from {_fmt_pct(gross_margins[0])} to {_fmt_pct(gross_margins[-1])}, which may indicate increasing competition, input cost inflation, or pricing pressure",
            data_reference=f"Margin trend: {' → '.join(_fmt_pct(m) for m in gross_margins[-5:])}",
        ))

    # Revenue deceleration
    growths = [m.revenue_growth for m in metrics[-4:] if m.revenue_growth is not None]
    if len(growths) >= 2 and growths[-1] is not None and growths[-2] is not None:
        if growths[-1] < growths[-2] and growths[-1] < 0.05:
            threats.append(SWOTItem(
                point="Decelerating growth trajectory",
                evidence=f"Revenue growth slowed from {_fmt_pct(growths[-2])} to {_fmt_pct(growths[-1])}, potentially indicating market saturation or competitive displacement",
                data_reference=f"Growth trend: {', '.join(_fmt_pct(g) for g in growths)}",
            ))

    # Rising debt
    debts = [s.total_debt for s in stmts if s.total_debt is not None]
    if len(debts) >= 3 and debts[-1] > debts[0] * 1.5:
        threats.append(SWOTItem(
            point="Rising debt levels",
            evidence=f"Total debt increased from {_fmt_num(debts[0])} to {_fmt_num(debts[-1])}, potentially constraining future financial flexibility and increasing risk in rising rate environment",
            data_reference=f"Debt trend: {' → '.join(_fmt_num(d) for d in debts[-5:])}",
        ))

    # Cyclicality
    revenue_vols = [m.revenue_growth for m in metrics if m.revenue_growth is not None]
    if revenue_vols:
        import statistics
        if len(revenue_vols) >= 3:
            vol = statistics.stdev(revenue_vols)
            if vol > 0.15:
                threats.append(SWOTItem(
                    point="High revenue cyclicality",
                    evidence=f"Revenue growth standard deviation of {_fmt_pct(vol)} indicates significant business cycle sensitivity, creating earnings uncertainty",
                    data_reference=f"Growth range: {_fmt_pct(min(revenue_vols))} to {_fmt_pct(max(revenue_vols))}",
                ))

    # Macro/sector threats
    threats.append(SWOTItem(
        point=f"Sector-specific regulatory and macro risks",
        evidence=f"The {sector}/{industry} sector faces ongoing regulatory changes, geopolitical tensions, and macroeconomic headwinds that could impact performance",
        data_reference=f"Sector: {sector}",
    ))

    return threats


def _build_summary(
    name: str,
    strengths: list[SWOTItem],
    weaknesses: list[SWOTItem],
    opportunities: list[SWOTItem],
    threats: list[SWOTItem],
) -> str:
    s_count = len(strengths)
    w_count = len(weaknesses)
    score = s_count + len(opportunities) - w_count - len(threats)

    if score >= 3:
        outlook = "predominantly positive"
    elif score >= 0:
        outlook = "balanced with moderate upside potential"
    else:
        outlook = "cautious with notable risks to monitor"

    top_s = strengths[0].point if strengths else "N/A"
    top_w = weaknesses[0].point if weaknesses else "N/A"

    return (
        f"Overall assessment for {name} is {outlook}. "
        f"Key strength: {top_s}. Key concern: {top_w}. "
        f"Identified {s_count} strengths, {w_count} weaknesses, "
        f"{len(opportunities)} opportunities, and {len(threats)} threats based on financial analysis."
    )
