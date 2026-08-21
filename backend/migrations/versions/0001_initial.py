"""Create the initial SpeakForge schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(100), nullable=False), sa.Column("email", sa.String(150), nullable=False), sa.Column("password", sa.String(255), nullable=False), sa.Column("role", sa.String(50)), sa.Column("is_verified", sa.Boolean()), sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()), sa.Column("reset_token", sa.String(255)), sa.Column("reset_token_expiry", sa.DateTime()))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("tests", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(255)), sa.Column("description", sa.String(500)), sa.Column("created_at", sa.DateTime()))
    op.create_table("questions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id")), sa.Column("question_text", sa.Text()), sa.Column("question_type", sa.String(20)), sa.Column("time_limit", sa.Integer()), sa.Column("order_number", sa.Integer()))
    op.create_table("question_answers", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("question_id", sa.Integer(), sa.ForeignKey("questions.id")), sa.Column("written_answer", sa.Text()), sa.Column("audio_path", sa.String(255)), sa.Column("transcribed_text", sa.Text()), sa.Column("grammar_score", sa.Integer()), sa.Column("fluency_score", sa.Integer()), sa.Column("final_score", sa.Integer()), sa.Column("grammar_errors", sa.Integer()), sa.Column("word_count", sa.Integer()), sa.Column("feedback", sa.Text()), sa.Column("created_at", sa.DateTime()))
    op.create_table("attempts", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id")), sa.Column("created_at", sa.DateTime()))
    op.create_table("results", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")), sa.Column("test_id", sa.Integer(), sa.ForeignKey("tests.id")), sa.Column("score", sa.Float()), sa.Column("answers", sa.JSON()), sa.Column("evaluation", sa.JSON()), sa.Column("submitted_at", sa.DateTime()))

def downgrade():
    for table in ("results", "attempts", "question_answers", "questions", "tests"):
        op.drop_table(table)
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
