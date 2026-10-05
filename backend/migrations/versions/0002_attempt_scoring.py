"""Keep attempts separate and persist scoring jobs and token revocation."""
from datetime import datetime
from alembic import op
import sqlalchemy as sa

revision = "0002_attempt_scoring"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("attempts", sa.Column("submitted_at", sa.DateTime()))
    op.add_column("question_answers", sa.Column("attempt_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_answer_attempt", "question_answers", "attempts", ["attempt_id"], ["id"])
    op.add_column("question_answers", sa.Column("score_status", sa.String(20), nullable=False, server_default="draft"))
    op.add_column("question_answers", sa.Column("score_error", sa.String(255)))
    op.add_column("question_answers", sa.Column("score_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("question_answers", sa.Column("score_started_at", sa.DateTime()))
    op.add_column("question_answers", sa.Column("score_token", sa.String(36)))
    op.alter_column("question_answers", "fluency_score", existing_type=sa.Integer(), type_=sa.Float())
    # Old answers had no attempt identity. Preserve each answer in a legacy attempt
    # rather than inventing groupings or deleting duplicates.
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT a.id, a.user_id, q.test_id, a.created_at, a.final_score FROM question_answers a JOIN questions q ON q.id=a.question_id")).mappings().all()
    for row in rows:
        created = row["created_at"] or datetime.utcnow()
        result = conn.execute(sa.text("INSERT INTO attempts(user_id,test_id,created_at,submitted_at) VALUES(:user,:test,:created,:created)"), {"user":row["user_id"],"test":row["test_id"],"created":created})
        conn.execute(sa.text("UPDATE question_answers SET attempt_id=:attempt, score_status=:status WHERE id=:id"), {"attempt":result.lastrowid,"status":"completed" if row["final_score"] is not None else "queued","id":row["id"]})
    op.create_unique_constraint("uq_attempt_question", "question_answers", ["attempt_id", "question_id"])
    op.create_index("ix_question_answers_attempt_id", "question_answers", ["attempt_id"])
    op.create_index("ix_question_answers_score_status", "question_answers", ["score_status"])


def downgrade():
    op.drop_constraint("fk_answer_attempt", "question_answers", type_="foreignkey")
    op.drop_index("ix_question_answers_score_status", table_name="question_answers")
    op.drop_index("ix_question_answers_attempt_id", table_name="question_answers")
    op.drop_constraint("uq_attempt_question", "question_answers", type_="unique")
    for name in ("score_token", "score_started_at", "score_attempts", "score_error", "score_status", "attempt_id"):
        op.drop_column("question_answers", name)
    op.drop_column("attempts", "submitted_at")
    op.drop_column("users", "token_version")
