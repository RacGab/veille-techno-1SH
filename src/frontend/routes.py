from flask import Blueprint, render_template, redirect, url_for
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import RagHistory, Ticket, TriageResult

frontend_bp = Blueprint("frontend", __name__)

@frontend_bp.route("/", methods=["GET"])
def index():
    return render_template("landing.html")

@frontend_bp.route("/portail", methods=["GET"])
def portail():
    return render_template("portail.html")

@frontend_bp.route("/dashboard", methods=["GET"])
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
