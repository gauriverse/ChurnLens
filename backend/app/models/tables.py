from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Float, ForeignKey, ForeignKeyConstraint,
    Index, Integer, Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database.base import Base, JsonType

# Mapped[str] means NOT NULL; Mapped[str | None] means the column may be empty.


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (CheckConstraint("row_count >= 0", name="row_count_nonneg"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    source: Mapped[str | None] = mapped_column(String(200))
    row_count: Mapped[int] = mapped_column(Integer)
    schema_json: Mapped[dict | None] = mapped_column(JsonType)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    is_reference: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
        CheckConstraint(
            "threshold IS NULL OR (threshold >= 0 AND threshold <= 1)",
            name="threshold_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(50))
    algorithm: Mapped[str] = mapped_column(String(200))
    training_dataset_id: Mapped[int | None] = mapped_column(
        ForeignKey("datasets.id", ondelete="SET NULL")
    )
    metrics: Mapped[dict | None] = mapped_column(JsonType)
    threshold: Mapped[float | None] = mapped_column(Float)
    artifact_path: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="status_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict | None] = mapped_column(JsonType)


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint(
            "dataset_id", "external_customer_id", name="uq_customers_dataset_external"
        ),
        CheckConstraint("tenure >= 0", name="tenure_nonneg"),
        CheckConstraint("monthly_charges >= 0", name="monthly_charges_nonneg"),
        CheckConstraint(
            "total_charges IS NULL OR total_charges >= 0", name="total_charges_nonneg"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"))
    external_customer_id: Mapped[str] = mapped_column(String(100))
    tenure: Mapped[int] = mapped_column(Integer)
    monthly_charges: Mapped[float] = mapped_column(Numeric(10, 2))
    total_charges: Mapped[float | None] = mapped_column(Numeric(12, 2))
    contract: Mapped[str | None] = mapped_column(String(50))
    payment_method: Mapped[str | None] = mapped_column(String(100))
    churned: Mapped[bool | None] = mapped_column(Boolean)  # empty when the label is unknown
    features: Mapped[dict] = mapped_column(JsonType)       # the full original row
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id", "customer_id", name="uq_predictions_run_customer"
        ),
        CheckConstraint(
            "churn_probability >= 0 AND churn_probability <= 1", name="probability_range"
        ),
        CheckConstraint(
            "risk_category IN ('Low', 'Medium', 'High')", name="risk_category_valid"
        ),
        CheckConstraint(
            "prediction_source IN ('out_of_fold_train', 'holdout_test', 'new_data')",
            name="source_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    churn_probability: Mapped[float] = mapped_column(Float)
    risk_category: Mapped[str] = mapped_column(String(10))
    prediction_source: Mapped[str] = mapped_column(String(30))
    reason_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Serves the risk-ranked customer table: "top N by probability for this run"
Index(
    "ix_predictions_run_probability",
    Prediction.analysis_run_id,
    Prediction.churn_probability.desc(),
)


class PredictionExplanation(Base):
    __tablename__ = "prediction_explanations"
    __table_args__ = (
        UniqueConstraint("prediction_id", "rank", name="uq_explanations_prediction_rank"),
        CheckConstraint("rank >= 1", name="rank_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE")
    )
    rank: Mapped[int] = mapped_column(Integer)
    feature: Mapped[str] = mapped_column(String(100))
    feature_value: Mapped[str | None] = mapped_column(String(100))
    shap_value: Mapped[float] = mapped_column(Float)  # log-odds units


class Segment(Base):
    __tablename__ = "segments"
    __table_args__ = (
        UniqueConstraint("analysis_run_id", "cluster_id", name="uq_segments_run_cluster"),
        CheckConstraint("size > 0", name="size_positive"),
        CheckConstraint("churn_rate >= 0 AND churn_rate <= 1", name="churn_rate_range"),
        CheckConstraint(
            "priority_tier IN ('High', 'Medium', 'Low')", name="tier_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    cluster_id: Mapped[int] = mapped_column(Integer)
    persona_name: Mapped[str] = mapped_column(String(200))
    size: Mapped[int] = mapped_column(Integer)
    churn_rate: Mapped[float] = mapped_column(Float)
    avg_monthly_charges: Mapped[float] = mapped_column(Numeric(10, 2))
    revenue_at_risk_12m: Mapped[float] = mapped_column(Numeric(14, 2))
    share_of_revenue_at_risk: Mapped[float] = mapped_column(Float)
    retention_priority: Mapped[int] = mapped_column(Integer)
    priority_tier: Mapped[str] = mapped_column(String(10))


class CustomerSegment(Base):
    """Each customer is in exactly one segment per analysis run (composite key)."""

    __tablename__ = "customer_segments"

    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), primary_key=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("segments.id", ondelete="CASCADE"), index=True
    )


class RetentionScenario(Base):
    __tablename__ = "retention_scenarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    analysis_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="SET NULL")
    )
    params: Mapped[dict] = mapped_column(JsonType)   # cost, success rate, threshold...
    results: Mapped[dict] = mapped_column(JsonType)  # hypothetical outcome
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RetentionRecommendation(Base):
    __tablename__ = "retention_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "analysis_run_id", "customer_id", name="uq_recommendations_run_customer"
        ),
        CheckConstraint("priority_rank >= 1", name="priority_rank_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE")
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    priority_rank: Mapped[int] = mapped_column(Integer)
    expected_value: Mapped[float] = mapped_column(Numeric(12, 2))
    reason_codes: Mapped[str | None] = mapped_column(String(300))
    suggested_action: Mapped[str | None] = mapped_column(Text)
    why_prioritized: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[dict | None] = mapped_column(JsonType)  # offer cost, success rate...
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


Index(
    "ix_recommendations_run_rank",
    RetentionRecommendation.analysis_run_id,
    RetentionRecommendation.priority_rank,
)