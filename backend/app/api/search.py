from __future__ import annotations

from flask import Blueprint, request
from sqlalchemy import or_

from ..models import Painting
from ..schemas import PaintingSchema

search_bp = Blueprint("search", __name__)
painting_schema = PaintingSchema()


@search_bp.get("")
def search():
    query = Painting.query
    term = request.args.get("q")
    folder = request.args.get("folder")
    tag = request.args.get("tag")
    image_format = request.args.get("format")

    if term:
        like = f"%{term}%"
        clauses = [Painting.title.ilike(like), Painting.tags.ilike(like)]
        if term.isdigit():
            clauses.append(Painting.id == int(term))
        query = query.filter(or_(*clauses))
    if folder:
        query = query.filter(Painting.folder == folder)
    if tag:
        query = query.filter(Painting.tags.ilike(f"%{tag}%"))
    if image_format:
        query = query.filter(Painting.format == image_format.upper())

    results = query.limit(50).all()
    return {"items": painting_schema.dump(results, many=True)}

