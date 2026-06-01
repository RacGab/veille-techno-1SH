from flask import Blueprint, render_template
from sqlalchemy.orm import joinedload

from extensions import db
from models import RagHistory, Ticket, TriageResult


frontend = Blueprint("frontend", __name__)


@frontend.route("/dashboard", methods=["GET"])
def dashboard():
    try:
        tickets = (
            Ticket.query.options(
                joinedload(Ticket.triage_result),
                joinedload(Ticket.rag_history),
            )
            .order_by(Ticket.date_creation.desc())
            .all()
        )

        return render_template("dashboard.html", tickets=tickets)

    except Exception as e:
        db.session.rollback()
        return render_template(
            "dashboard.html",
            tickets=[],
            erreur=f"Impossible de charger les billets : {str(e)}",
        ), 500
