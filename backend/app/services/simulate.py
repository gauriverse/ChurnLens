import pandas as pd
from sqlalchemy import Float, and_, cast, select
from sqlalchemy.orm import Session

from backend.app.models.tables import Customer, CustomerSegment, Prediction, Segment
from churnlens.simulator.scenarios import select_targets, summarize_targets

NO_SEGMENT = "No segment"


def load_population(db: Session, run_id: int):
    """Every scored customer in the run: probability, monthly charge and segment name."""
    rows = db.execute(
        select(
            Prediction.churn_probability,
            cast(Customer.monthly_charges, Float),
            Segment.persona_name,
        )
        .select_from(Prediction)
        .join(Customer, Customer.id == Prediction.customer_id)
        .outerjoin(
            CustomerSegment,
            and_(
                CustomerSegment.customer_id == Customer.id,
                CustomerSegment.analysis_run_id == run_id,
            ),
        )
        .outerjoin(Segment, Segment.id == CustomerSegment.segment_id)
        .where(Prediction.analysis_run_id == run_id)
        .order_by(Prediction.id)  # fixed order, so ties are always broken the same way
    ).all()
    population = pd.DataFrame(
        rows, columns=["churn_probability", "MonthlyCharges", "persona_name"]
    )
    population["persona_name"] = population["persona_name"].fillna(NO_SEGMENT)
    return population


def value_basis(margin):
    return "revenue" if margin == 1.0 else f"revenue x {margin:g} assumed margin"


def scenario_warnings(*, targeted, eligible, negative_value, net_benefit, max_customers):
    """Plain-language flags, built only from the scenario's own numbers."""
    if targeted == 0:
        return [
            "No offers are made under these rules (no customer meets the risk threshold, "
            "or the cap is 0), so every outcome is zero."
        ]
    warnings = []
    if negative_value:
        warnings.append(
            "Contacted customers with a negative expected value under these assumptions: "
            f"{negative_value} of {targeted}. Contacting them is expected to cost more than it "
            "preserves; a higher risk threshold or a smaller customer cap would avoid them."
        )
    if net_benefit < 0:
        warnings.append(
            "Expected net benefit is negative under these assumptions: the campaign is "
            "expected to cost more than the value it preserves."
        )
    if max_customers is not None and eligible < max_customers:
        warnings.append(
            f"Only {eligible} customers meet the risk threshold, so the cap of "
            f"{max_customers} offers was not reached."
        )
    return warnings


def simulate_scenario(population, s):
    """Run one scenario (a ScenarioInput) on the population and format the result."""
    targets = select_targets(
        population, offer_cost=s.offer_cost, success_rate=s.success_rate,
        risk_threshold=s.risk_threshold, max_customers=s.max_customers,
        horizon_months=s.horizon_months, margin=s.margin,
    )
    summary = summarize_targets(targets, s.offer_cost)
    eligible = int((population["churn_probability"] >= s.risk_threshold).sum())
    negative_value = int((targets["expected_value"] < 0).sum())

    by_segment = []
    if len(targets):
        grouped = (
            targets.groupby("persona_name")
            .agg(
                n=("expected_value", "size"),
                revenue=("revenue_preserved", "sum"),
                net=("expected_value", "sum"),
            )
            .sort_values("net", ascending=False, kind="mergesort")
        )
        by_segment = [
            {
                "persona_name": name,
                "customers_targeted": int(row["n"]),
                "campaign_cost": round(int(row["n"]) * s.offer_cost, 2),
                "expected_revenue_preserved": round(float(row["revenue"]), 2),
                "expected_net_benefit": round(float(row["net"]), 2),
            }
            for name, row in grouped.iterrows()
        ]

    roi = summary["expected_roi"]
    return {
        "name": s.name,
        "assumptions": s.model_dump(exclude={"name"}),
        "customers_eligible": eligible,
        "customers_targeted": summary["customers_targeted"],
        "campaign_cost": round(summary["campaign_cost"], 2),
        "expected_retained_customers": round(summary["expected_retained_customers"], 2),
        "expected_revenue_preserved": round(summary["expected_revenue_preserved"], 2),
        "expected_net_benefit": round(summary["expected_net_benefit"], 2),
        "expected_roi": None if roi != roi else round(roi, 2),  # roi != roi is true only for NaN
        "value_basis": value_basis(s.margin),
        "by_segment": by_segment,
        "warnings": scenario_warnings(
            targeted=summary["customers_targeted"], eligible=eligible,
            negative_value=negative_value, net_benefit=summary["expected_net_benefit"],
            max_customers=s.max_customers,
        ),
    }