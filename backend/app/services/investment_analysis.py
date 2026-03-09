"""Investment analysis engine: thesis, catalysts, target price, risks."""

import statistics
from typing import Optional

from ..models.schemas import (
    InvestmentAnalysis, InvestmentAnalysisItem,
    TargetPriceAnalysis, PriceScenario,
    FinancialStatement, FinancialMetrics,
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
    return items[-n:] if len(items) >= n else items


def _avg(values: list[float | None]) -> float | None:
    valid = [v for v in values if v is not None]
    return sum(valid) / len(valid) if valid else None


def generate_investment_analysis(
    company_name: str,
    sector: str,
    industry: str,
    statements: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    current_price: float,
    market_cap: float,
    beta: float,
    currency: str,
) -> InvestmentAnalysis:
    """Generate comprehensive investment analysis."""
    thesis = _build_investment_thesis(company_name, statements, metrics, sector)
    catalysts = _build_key_catalysts(statements, metrics, sector, industry)
    target = _build_target_price(
        company_name, statements, metrics, current_price, market_cap, currency
    )
    risks = _build_key_risks(statements, metrics, sector, industry, beta)

    # Determine recommendation
    if target.upside_pct > 15:
        recommendation = "매수"
    elif target.upside_pct > -10:
        recommendation = "보유"
    else:
        recommendation = "매도"

    # Build summary
    summary = _build_summary(company_name, thesis, catalysts, target, risks, recommendation)

    return InvestmentAnalysis(
        investment_thesis=thesis,
        key_catalysts=catalysts,
        target_price=target,
        key_risks=risks,
        summary=summary,
        recommendation=recommendation,
    )


def _build_investment_thesis(
    name: str,
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    sector: str,
) -> list[InvestmentAnalysisItem]:
    items = []
    recent_m = _recent(metrics)
    recent_s = _recent(stmts)

    # Growth analysis
    growths = [m.revenue_growth for m in metrics if m.revenue_growth is not None]
    avg_growth = _avg(growths)
    recent_growth = _avg([m.revenue_growth for m in recent_m])

    if recent_growth is not None and recent_growth > 0.05:
        items.append(InvestmentAnalysisItem(
            title="성장성 확보",
            content=f"최근 3년 평균 매출 성장률 {_fmt_pct(recent_growth)}로 안정적인 성장 기반을 보유하고 있습니다. "
                    f"{'장기 CAGR ' + _fmt_pct(avg_growth) + ' 대비 성장 가속화 추세입니다.' if avg_growth and recent_growth > avg_growth else '장기 성장 추세에 부합하는 성장률입니다.'}",
            details=[
                f"최근 3년 평균 매출 성장률: {_fmt_pct(recent_growth)}",
                f"전체 기간 평균 성장률: {_fmt_pct(avg_growth)}",
                f"매출 추이: {' → '.join(_fmt_num(s.revenue) for s in stmts[-5:])}",
            ],
        ))
    elif recent_growth is not None:
        items.append(InvestmentAnalysisItem(
            title="성장 둔화 우려",
            content=f"최근 3년 평균 매출 성장률이 {_fmt_pct(recent_growth)}로 저조합니다. "
                    f"신규 성장 동력 확보 여부가 투자 판단의 핵심입니다.",
            details=[
                f"최근 3년 평균 매출 성장률: {_fmt_pct(recent_growth)}",
                f"전체 기간 평균 성장률: {_fmt_pct(avg_growth)}",
            ],
        ))

    # Profitability
    avg_op_margin = _avg([m.operating_margin for m in recent_m])
    avg_roe = _avg([m.roe for m in recent_m])

    if avg_op_margin is not None and avg_roe is not None:
        if avg_op_margin > 0.15 and avg_roe > 0.12:
            items.append(InvestmentAnalysisItem(
                title="우수한 수익성",
                content=f"영업이익률 {_fmt_pct(avg_op_margin)}, ROE {_fmt_pct(avg_roe)}로 "
                        f"업종 내 높은 수익성을 유지하고 있어 경쟁 우위를 확인할 수 있습니다.",
                details=[
                    f"영업이익률: {', '.join(_fmt_pct(m.operating_margin) for m in recent_m)}",
                    f"ROE: {', '.join(_fmt_pct(m.roe) for m in recent_m)}",
                    f"순이익률: {', '.join(_fmt_pct(m.net_margin) for m in recent_m)}",
                ],
            ))
        elif avg_op_margin < 0.05:
            items.append(InvestmentAnalysisItem(
                title="낮은 수익성",
                content=f"영업이익률 {_fmt_pct(avg_op_margin)}로 수익성이 낮은 편입니다. "
                        f"비용 구조 개선 없이는 주주가치 창출이 어려울 수 있습니다.",
                details=[
                    f"영업이익률: {', '.join(_fmt_pct(m.operating_margin) for m in recent_m)}",
                    f"ROE: {', '.join(_fmt_pct(m.roe) for m in recent_m)}",
                ],
            ))

    # Cash generation
    avg_fcf_margin = _avg([m.fcf_margin for m in recent_m])
    if avg_fcf_margin is not None:
        if avg_fcf_margin > 0.10:
            items.append(InvestmentAnalysisItem(
                title="강건한 현금 창출력",
                content=f"FCF 마진 {_fmt_pct(avg_fcf_margin)}로 풍부한 잉여현금흐름을 창출하고 있습니다. "
                        f"배당 확대, 자사주 매입, 전략적 M&A 등 주주환원 여력이 충분합니다.",
                details=[
                    f"FCF: {', '.join(_fmt_num(s.free_cash_flow) for s in recent_s)}",
                    f"FCF 마진: {', '.join(_fmt_pct(m.fcf_margin) for m in recent_m)}",
                ],
            ))
        elif avg_fcf_margin < 0:
            items.append(InvestmentAnalysisItem(
                title="현금흐름 적자",
                content=f"FCF 마진 {_fmt_pct(avg_fcf_margin)}로 잉여현금흐름이 부족합니다. "
                        f"대규모 투자 사이클이 원인일 수 있으나, 지속될 경우 재무 건전성에 부담이 됩니다.",
                details=[
                    f"FCF: {', '.join(_fmt_num(s.free_cash_flow) for s in recent_s)}",
                ],
            ))

    # Balance sheet strength
    avg_de = _avg([m.debt_to_equity for m in recent_m])
    if recent_s and recent_s[-1].cash_and_equivalents and recent_s[-1].total_debt:
        net_cash = recent_s[-1].cash_and_equivalents - recent_s[-1].total_debt
        if net_cash > 0:
            items.append(InvestmentAnalysisItem(
                title="순현금 보유 기업",
                content=f"부채보다 현금이 {_fmt_num(net_cash)} 많은 순현금 상태로, "
                        f"재무 안정성이 높고 위기 대응 능력이 우수합니다.",
                details=[
                    f"현금: {_fmt_num(recent_s[-1].cash_and_equivalents)}",
                    f"총부채: {_fmt_num(recent_s[-1].total_debt)}",
                    f"순현금: {_fmt_num(net_cash)}",
                ],
            ))
        elif avg_de is not None and avg_de > 2.0:
            items.append(InvestmentAnalysisItem(
                title="높은 재무 레버리지",
                content=f"D/E 비율 {avg_de:.2f}x로 레버리지가 높은 편입니다. "
                        f"금리 상승기에 이자 비용 부담이 증가할 수 있습니다.",
                details=[
                    f"D/E: {', '.join(f'{m.debt_to_equity:.2f}x' if m.debt_to_equity else 'N/A' for m in recent_m)}",
                ],
            ))

    if not items:
        items.append(InvestmentAnalysisItem(
            title="제한적 데이터",
            content="현재 보유한 재무 데이터만으로는 명확한 투자 논리를 도출하기 어렵습니다. "
                    "정성적 분석과 업종 분석을 병행할 것을 권장합니다.",
            details=[],
        ))

    return items


def _build_key_catalysts(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    sector: str,
    industry: str,
) -> list[InvestmentAnalysisItem]:
    catalysts = []
    recent_m = _recent(metrics)
    recent_s = _recent(stmts)

    # Growth acceleration
    growths = [m.revenue_growth for m in metrics[-4:] if m.revenue_growth is not None]
    if len(growths) >= 2 and growths[-1] is not None and growths[-2] is not None:
        if growths[-1] > growths[-2] and growths[-1] > 0:
            catalysts.append(InvestmentAnalysisItem(
                title="매출 성장 가속화 [상승 트리거]",
                content=f"매출 성장률이 {_fmt_pct(growths[-2])}에서 {_fmt_pct(growths[-1])}로 가속화되고 있습니다. "
                        f"이 추세가 지속된다면 실적 컨센서스 상향 조정의 기폭제가 될 수 있습니다.",
                details=[
                    f"성장률 추이: {', '.join(_fmt_pct(g) for g in growths)}",
                    "컨센서스 상향 시 멀티플 확장 기대",
                ],
            ))
        elif growths[-1] < growths[-2] and growths[-1] < 0.03:
            catalysts.append(InvestmentAnalysisItem(
                title="매출 성장 둔화 [하락 트리거]",
                content=f"매출 성장률이 {_fmt_pct(growths[-2])}에서 {_fmt_pct(growths[-1])}로 둔화되고 있습니다. "
                        f"추세 반전 없이 지속될 경우 실적 하향 조정이 불가피합니다.",
                details=[
                    f"성장률 추이: {', '.join(_fmt_pct(g) for g in growths)}",
                ],
            ))

    # Margin expansion/contraction
    op_margins = [m.operating_margin for m in metrics if m.operating_margin is not None]
    if len(op_margins) >= 3:
        if op_margins[-1] > op_margins[-2] > op_margins[-3]:
            catalysts.append(InvestmentAnalysisItem(
                title="수익성 개선 추세 [상승 트리거]",
                content="영업이익률이 3년 연속 개선되고 있으며, 이는 운영 효율화 또는 매출 믹스 개선을 반영합니다. "
                        "수익성 개선이 시장에 인식되면 밸류에이션 리레이팅이 발생할 수 있습니다.",
                details=[
                    f"영업이익률 추이: {', '.join(_fmt_pct(m) for m in op_margins[-3:])}",
                ],
            ))
        elif op_margins[-1] < op_margins[-2] < op_margins[-3]:
            catalysts.append(InvestmentAnalysisItem(
                title="수익성 악화 추세 [하락 트리거]",
                content="영업이익률이 3년 연속 하락하고 있으며, 비용 압박이나 경쟁 심화의 신호일 수 있습니다.",
                details=[
                    f"영업이익률 추이: {', '.join(_fmt_pct(m) for m in op_margins[-3:])}",
                ],
            ))

    # CAPEX cycle (investment for future growth)
    if recent_s and recent_s[-1].capital_expenditure and recent_s[-1].revenue:
        capex_ratio = abs(recent_s[-1].capital_expenditure) / recent_s[-1].revenue
        if capex_ratio > 0.10:
            catalysts.append(InvestmentAnalysisItem(
                title="대규모 설비투자 회수 기대 [상승 트리거]",
                content=f"매출 대비 CAPEX 비율이 {_fmt_pct(capex_ratio)}로 적극적인 투자 중입니다. "
                        f"투자 사이클 완료 후 감가상각 부담 감소와 함께 수익성 개선이 기대됩니다.",
                details=[
                    f"CAPEX: {_fmt_num(abs(recent_s[-1].capital_expenditure))}",
                    f"매출 대비 비율: {_fmt_pct(capex_ratio)}",
                ],
            ))

    # Dividend potential
    if recent_s and recent_s[-1].dividends_paid and recent_s[-1].net_income:
        payout = abs(recent_s[-1].dividends_paid) / recent_s[-1].net_income if recent_s[-1].net_income > 0 else 0
        if payout < 0.3 and recent_s[-1].free_cash_flow and recent_s[-1].free_cash_flow > 0:
            catalysts.append(InvestmentAnalysisItem(
                title="배당 확대 여력 [상승 트리거]",
                content=f"배당성향이 {_fmt_pct(payout)}로 낮은 편이며, FCF가 충분하여 배당 확대 가능성이 있습니다. "
                        f"주주환원 정책 강화 시 밸류에이션 프리미엄 부여가 가능합니다.",
                details=[
                    f"배당성향: {_fmt_pct(payout)}",
                    f"FCF: {_fmt_num(recent_s[-1].free_cash_flow)}",
                ],
            ))

    # Sector-specific
    sector_lower = (sector or "").lower()
    if "technology" in sector_lower or "semiconductor" in (industry or "").lower():
        catalysts.append(InvestmentAnalysisItem(
            title="AI/반도체 수요 확대 [업종 트리거]",
            content="AI 인프라 투자 확대에 따른 반도체·기술 수요 증가가 실적 개선의 구조적 동력이 될 수 있습니다.",
            details=["AI 데이터센터 투자 증가", "HBM/고대역폭 메모리 수요 확대", "클라우드 CAPEX 확대 추세"],
        ))
    elif "consumer" in sector_lower:
        catalysts.append(InvestmentAnalysisItem(
            title="소비 회복 시 수혜 [업종 트리거]",
            content="소비심리 회복 및 실질 소득 증가 시, 소비재 섹터 전반의 실적 개선이 기대됩니다.",
            details=["금리 인하 사이클 시 소비 여력 확대", "프리미엄 제품 수요 회복 가능성"],
        ))
    elif "financial" in sector_lower:
        catalysts.append(InvestmentAnalysisItem(
            title="금리 환경 변화 [업종 트리거]",
            content="금리 정책 변화에 따라 순이자마진(NIM) 및 자산 건전성에 직접적 영향을 받으며, "
                    "금리 안정화 시 밸류에이션 회복이 기대됩니다.",
            details=["NIM 개선 가능성", "자산 건전성 지표 모니터링 필요"],
        ))

    if not catalysts:
        catalysts.append(InvestmentAnalysisItem(
            title="뚜렷한 단기 트리거 부재",
            content="현재 재무 데이터상 명확한 주가 상승/하락 트리거를 식별하기 어렵습니다. "
                    "업종 동향 및 경영진 가이던스를 추가로 확인해야 합니다.",
            details=[],
        ))

    return catalysts


def _build_target_price(
    name: str,
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    current_price: float,
    market_cap: float,
    currency: str,
) -> TargetPriceAnalysis:
    recent_s = _recent(stmts)
    recent_m = _recent(metrics)
    latest = stmts[-1] if stmts else None

    # Method 1: P/E based
    pe_target = None
    if latest and latest.eps and latest.eps > 0 and current_price > 0:
        current_pe = current_price / latest.eps
        # Use trailing 3-year avg EPS growth to project next year EPS
        eps_values = [s.eps for s in stmts[-4:] if s.eps and s.eps > 0]
        if len(eps_values) >= 2:
            eps_growth = (eps_values[-1] / eps_values[0]) ** (1 / (len(eps_values) - 1)) - 1
            projected_eps = latest.eps * (1 + eps_growth)
            # Target P/E: use historical average, capped at reasonable range
            target_pe = min(max(current_pe * 0.9, 8), 35)
            pe_target = projected_eps * target_pe

    # Method 2: EV/EBITDA based
    ev_ebitda_target = None
    if latest and latest.ebitda and latest.ebitda > 0 and market_cap > 0:
        total_debt = latest.total_debt or 0
        cash = latest.cash_and_equivalents or 0
        ev = market_cap + total_debt - cash
        current_ev_ebitda = ev / latest.ebitda if latest.ebitda > 0 else 10

        # Project next year EBITDA
        ebitda_margins = [s.ebitda / s.revenue for s in stmts[-3:]
                         if s.ebitda and s.revenue and s.revenue > 0]
        avg_ebitda_margin = sum(ebitda_margins) / len(ebitda_margins) if ebitda_margins else 0.15

        growths = [m.revenue_growth for m in metrics[-3:] if m.revenue_growth is not None]
        avg_growth = sum(growths) / len(growths) if growths else 0.05
        projected_revenue = latest.revenue * (1 + avg_growth) if latest.revenue else 0
        projected_ebitda = projected_revenue * avg_ebitda_margin

        target_ev_ebitda = min(max(current_ev_ebitda * 0.95, 4), 20)
        target_ev = projected_ebitda * target_ev_ebitda
        target_equity = target_ev - total_debt + cash
        shares = latest.shares_outstanding or 1
        ev_ebitda_target = target_equity / shares

    # Combine methods
    targets = [t for t in [pe_target, ev_ebitda_target] if t is not None and t > 0]
    if targets:
        base_target = sum(targets) / len(targets)
    elif current_price > 0:
        base_target = current_price  # fallback
    else:
        base_target = 0

    upside = ((base_target / current_price) - 1) * 100 if current_price > 0 else 0

    # Build assumptions list
    assumptions = []
    if pe_target:
        assumptions.append(f"P/E 기반 목표가: {currency} {pe_target:,.0f}")
    if ev_ebitda_target:
        assumptions.append(f"EV/EBITDA 기반 목표가: {currency} {ev_ebitda_target:,.0f}")

    recent_growth_vals = [m.revenue_growth for m in metrics[-3:] if m.revenue_growth is not None]
    if recent_growth_vals:
        assumptions.append(f"적용 매출 성장률: {_fmt_pct(sum(recent_growth_vals)/len(recent_growth_vals))}")

    ebitda_m = [s.ebitda / s.revenue for s in stmts[-3:]
                if s.ebitda and s.revenue and s.revenue > 0]
    if ebitda_m:
        assumptions.append(f"적용 EBITDA 마진: {_fmt_pct(sum(ebitda_m)/len(ebitda_m))}")

    if pe_target and latest and latest.eps:
        assumptions.append(f"현재 EPS: {currency} {latest.eps:,.0f}")

    methodology_parts = []
    if pe_target and ev_ebitda_target:
        methodology_parts.append("P/E 멀티플과 EV/EBITDA 멀티플의 평균으로 목표가를 산출했습니다")
    elif pe_target:
        methodology_parts.append("P/E 멀티플 기반으로 목표가를 산출했습니다")
    elif ev_ebitda_target:
        methodology_parts.append("EV/EBITDA 멀티플 기반으로 목표가를 산출했습니다")
    else:
        methodology_parts.append("충분한 데이터가 없어 현재가를 기준으로 합니다")

    methodology = ". ".join(methodology_parts) + "."

    # Scenarios
    bull_target = base_target * 1.20
    bear_target = base_target * 0.80

    scenarios = [
        PriceScenario(
            name="낙관 시나리오",
            target_price=round(bull_target, 2),
            reasoning="매출 성장 가속화, 수익성 개선, 멀티플 확장이 동시에 발생하는 최상의 시나리오",
        ),
        PriceScenario(
            name="기본 시나리오",
            target_price=round(base_target, 2),
            reasoning="현재 추세가 유지되는 가운데 점진적인 실적 개선이 반영된 시나리오",
        ),
        PriceScenario(
            name="비관 시나리오",
            target_price=round(bear_target, 2),
            reasoning="매출 둔화, 마진 압박, 멀티플 축소가 발생하는 하방 리스크 시나리오",
        ),
    ]

    return TargetPriceAnalysis(
        current_price=current_price,
        target_price=round(base_target, 2),
        upside_pct=round(upside, 1),
        methodology=methodology,
        assumptions=assumptions,
        scenarios=scenarios,
    )


def _build_key_risks(
    stmts: list[FinancialStatement],
    metrics: list[FinancialMetrics],
    sector: str,
    industry: str,
    beta: float,
) -> list[InvestmentAnalysisItem]:
    risks = []
    recent_m = _recent(metrics)

    # Earnings volatility
    net_incomes = [s.net_income for s in stmts if s.net_income is not None]
    if net_incomes:
        neg_years = sum(1 for ni in net_incomes if ni < 0)
        if neg_years > 0:
            risks.append(InvestmentAnalysisItem(
                title="실적 변동성 리스크",
                content=f"과거 {len(net_incomes)}년 중 {neg_years}년 순손실을 기록했습니다. "
                        f"경기 사이클에 민감한 사업 구조일 수 있으며, 하방 리스크가 존재합니다.",
                details=[
                    f"순이익 추이: {', '.join(_fmt_num(ni) for ni in net_incomes[-5:])}",
                    f"손실 발생 연도: {neg_years}/{len(net_incomes)}년",
                ],
            ))

    # Revenue volatility
    rev_growths = [m.revenue_growth for m in metrics if m.revenue_growth is not None]
    if len(rev_growths) >= 3:
        vol = statistics.stdev(rev_growths)
        if vol > 0.15:
            risks.append(InvestmentAnalysisItem(
                title="높은 매출 변동성",
                content=f"매출 성장률의 표준편차가 {_fmt_pct(vol)}로 높아 사업의 예측 가능성이 낮습니다. "
                        f"경기 순환 또는 특정 고객 의존도가 높을 가능성이 있습니다.",
                details=[
                    f"성장률 범위: {_fmt_pct(min(rev_growths))} ~ {_fmt_pct(max(rev_growths))}",
                    f"표준편차: {_fmt_pct(vol)}",
                ],
            ))

    # Margin pressure
    gross_margins = [m.gross_margin for m in metrics if m.gross_margin is not None]
    if len(gross_margins) >= 3 and gross_margins[-1] < gross_margins[0]:
        decline = gross_margins[0] - gross_margins[-1]
        risks.append(InvestmentAnalysisItem(
            title="마진 압박 리스크",
            content=f"매출총이익률이 {_fmt_pct(gross_margins[0])}에서 {_fmt_pct(gross_margins[-1])}로 "
                    f"{_fmt_pct(decline)} 하락했습니다. 원가 상승, 경쟁 심화 등으로 수익성이 구조적으로 "
                    f"악화될 가능성을 주시해야 합니다.",
            details=[
                f"매출총이익률 추이: {' → '.join(_fmt_pct(m) for m in gross_margins[-5:])}",
            ],
        ))

    # Leverage risk
    avg_de = _avg([m.debt_to_equity for m in recent_m])
    avg_ic = _avg([m.interest_coverage for m in recent_m])
    if avg_de is not None and avg_de > 1.5:
        risks.append(InvestmentAnalysisItem(
            title="재무 레버리지 리스크",
            content=f"D/E 비율 {avg_de:.2f}x로 부채 수준이 높습니다. "
                    f"금리 상승기에는 이자 비용 증가로 수익성 압박이 가중될 수 있습니다.",
            details=[
                f"D/E: {', '.join(f'{m.debt_to_equity:.2f}x' if m.debt_to_equity else 'N/A' for m in recent_m)}",
                f"이자보상배율: {f'{avg_ic:.1f}x' if avg_ic else 'N/A'}",
            ],
        ))

    # High beta / market risk
    if beta > 1.3:
        risks.append(InvestmentAnalysisItem(
            title="시장 민감도 높음",
            content=f"베타가 {beta:.2f}로 시장 대비 변동성이 큽니다. "
                    f"시장 하락 국면에서 동종업종 대비 더 큰 손실을 볼 수 있습니다.",
            details=[
                f"베타: {beta:.2f}",
                "시장 10% 하락 시 해당 종목은 약 " + f"{beta * 10:.0f}% 하락 가능",
            ],
        ))

    # Macro / sector risks
    risks.append(InvestmentAnalysisItem(
        title="거시경제 및 업종 리스크",
        content=f"{sector}/{industry} 업종은 규제 변화, 지정학적 리스크, 거시경제 불확실성에 "
                f"영향을 받을 수 있습니다. 특히 글로벌 공급망 변화와 통상 정책 변화에 주의가 필요합니다.",
        details=[
            "글로벌 경기 둔화 가능성",
            "환율 변동 리스크",
            f"{sector} 업종 규제 강화 가능성",
            "지정학적 리스크 (공급망 재편)",
        ],
    ))

    return risks


def _build_summary(
    name: str,
    thesis: list[InvestmentAnalysisItem],
    catalysts: list[InvestmentAnalysisItem],
    target: TargetPriceAnalysis,
    risks: list[InvestmentAnalysisItem],
    recommendation: str,
) -> str:
    upside_str = f"+{target.upside_pct:.1f}%" if target.upside_pct > 0 else f"{target.upside_pct:.1f}%"

    return (
        f"{name}에 대한 투자의견은 '{recommendation}'이며, "
        f"목표가 {target.target_price:,.0f} (현재가 대비 {upside_str})입니다. "
        f"투자 논리 {len(thesis)}건, 핵심 트리거 {len(catalysts)}건, "
        f"주요 리스크 {len(risks)}건을 기반으로 분석했습니다."
    )
