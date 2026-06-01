from datetime import datetime, timezone

from .extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    statut = db.Column(db.String(50), nullable=False, default="nouveau")
    date_creation = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    date_modification = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    triage_result = db.relationship(
        "TriageResult",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )
    rag_history = db.relationship(
        "RagHistory",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="RagHistory.date_creation.desc()",
    )

    def __repr__(self):
        return f"<Ticket id={self.id} statut={self.statut}>"

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "statut": self.statut,
            "date_creation": self.date_creation.isoformat()
            if self.date_creation
            else None,
            "date_modification": self.date_modification.isoformat()
            if self.date_modification
            else None,
            "triage_result": self.triage_result.to_dict()
            if self.triage_result
            else None,
        }


class TriageResult(db.Model):
    __tablename__ = "triage_results"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    categorie = db.Column(db.String(50), nullable=False)
    priorite = db.Column(db.String(50), nullable=False)
    justification = db.Column(db.Text, nullable=False)
    tokens_utilises = db.Column(db.Integer, nullable=True)
    modele_ia = db.Column(db.String(100), nullable=False, default="gemini-2.5-flash")
    date_creation = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    ticket = db.relationship("Ticket", back_populates="triage_result")

    def __repr__(self):
        return (
            f"<TriageResult id={self.id} ticket_id={self.ticket_id} "
            f"categorie={self.categorie} priorite={self.priorite}>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "categorie": self.categorie,
            "priorite": self.priorite,
            "justification": self.justification,
            "tokens_utilises": self.tokens_utilises,
            "modele_ia": self.modele_ia,
            "date_creation": self.date_creation.isoformat()
            if self.date_creation
            else None,
        }


class RagHistory(db.Model):
    __tablename__ = "rag_history"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(
        db.Integer,
        db.ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    contexte_retrouve = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255), nullable=True)
    score_similarite = db.Column(db.Float, nullable=True)
    categorie_reference = db.Column(db.String(50), nullable=True)
    priorite_reference = db.Column(db.String(50), nullable=True)
    date_creation = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    ticket = db.relationship("Ticket", back_populates="rag_history")

    def __repr__(self):
        return f"<RagHistory id={self.id} ticket_id={self.ticket_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "contexte_retrouve": self.contexte_retrouve,
            "source": self.source,
            "score_similarite": self.score_similarite,
            "categorie_reference": self.categorie_reference,
            "priorite_reference": self.priorite_reference,
            "date_creation": self.date_creation.isoformat()
            if self.date_creation
            else None,
        }
