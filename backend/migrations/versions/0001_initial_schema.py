"""Create the synthetic network analysis schema.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=40), nullable=False, unique=True),
    )
    op.create_index("ix_entity_types_name", "entity_types", ["name"])
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "entities",
        sa.Column("id", sa.String(length=40), primary_key=True),
        sa.Column("entity_type", sa.String(length=40), sa.ForeignKey("entity_types.name"), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("extra_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_entities_entity_type", "entities", ["entity_type"])
    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_entity_id", sa.String(length=40), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_entity_id", sa.String(length=40), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_relationships_source_entity_id", "relationships", ["source_entity_id"])
    op.create_index("ix_relationships_target_entity_id", "relationships", ["target_entity_id"])
    op.create_index("ix_relationships_relationship_type", "relationships", ["relationship_type"])
    op.create_index("ix_relationship_source_target", "relationships", ["source_entity_id", "target_entity_id"])
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(length=40), nullable=False, unique=True),
        sa.Column("source_entity_id", sa.String(length=40), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("target_entity_id", sa.String(length=40), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount >= 0", name="ck_transaction_amount_nonnegative"),
    )
    op.create_index("ix_transactions_source_entity_id", "transactions", ["source_entity_id"])
    op.create_index("ix_transactions_target_entity_id", "transactions", ["target_entity_id"])
    op.create_index("ix_transactions_occurred_at", "transactions", ["occurred_at"])
    op.create_table(
        "communications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_entity_id", sa.String(length=40), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("target_entity_id", sa.String(length=40), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_communications_source_entity_id", "communications", ["source_entity_id"])
    op.create_index("ix_communications_target_entity_id", "communications", ["target_entity_id"])
    op.create_index("ix_communications_occurred_at", "communications", ["occurred_at"])
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_id", sa.String(length=40), sa.ForeignKey("entities.id"), nullable=False),
        sa.Column("location_code", sa.String(length=40), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_locations_entity_id", "locations", ["entity_id"])
    op.create_index("ix_locations_location_code", "locations", ["location_code"])
    op.create_index("ix_locations_occurred_at", "locations", ["occurred_at"])
    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference_id", sa.String(length=40), nullable=False, unique=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("selected_entities", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_investigations_reference_id", "investigations", ["reference_id"])
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("investigation_id", sa.Integer(), sa.ForeignKey("investigations.id"), nullable=True),
        sa.Column("result_type", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analysis_results_result_type", "analysis_results", ["result_type"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_index("ix_analysis_results_result_type", table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_index("ix_investigations_reference_id", table_name="investigations")
    op.drop_table("investigations")
    op.drop_index("ix_locations_occurred_at", table_name="locations")
    op.drop_index("ix_locations_location_code", table_name="locations")
    op.drop_index("ix_locations_entity_id", table_name="locations")
    op.drop_table("locations")
    op.drop_index("ix_communications_occurred_at", table_name="communications")
    op.drop_index("ix_communications_target_entity_id", table_name="communications")
    op.drop_index("ix_communications_source_entity_id", table_name="communications")
    op.drop_table("communications")
    op.drop_index("ix_transactions_occurred_at", table_name="transactions")
    op.drop_index("ix_transactions_target_entity_id", table_name="transactions")
    op.drop_index("ix_transactions_source_entity_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_relationship_source_target", table_name="relationships")
    op.drop_index("ix_relationships_relationship_type", table_name="relationships")
    op.drop_index("ix_relationships_target_entity_id", table_name="relationships")
    op.drop_index("ix_relationships_source_entity_id", table_name="relationships")
    op.drop_table("relationships")
    op.drop_index("ix_entities_entity_type", table_name="entities")
    op.drop_table("entities")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_entity_types_name", table_name="entity_types")
    op.drop_table("entity_types")
