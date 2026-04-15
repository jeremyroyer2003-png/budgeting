from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Category

categories_bp = Blueprint("categories", __name__)


@categories_bp.get("/")
def list_categories():
    cats = Category.query.order_by(Category.type, Category.name).all()
    return jsonify([c.to_dict() for c in cats])


@categories_bp.post("/")
def create_category():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("type"):
        return jsonify({"error": "name and type are required"}), 400

    if Category.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Category name already exists"}), 409

    cat = Category(
        name=data["name"],
        type=data["type"],
        color=data.get("color", "#6366F1"),
        icon=data.get("icon", "tag"),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@categories_bp.put("/<int:cat_id>")
def update_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    data = request.get_json()
    if "name" in data:
        cat.name = data["name"]
    if "color" in data:
        cat.color = data["color"]
    if "icon" in data:
        cat.icon = data["icon"]
    db.session.commit()
    return jsonify(cat.to_dict())


@categories_bp.delete("/<int:cat_id>")
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.is_system:
        return jsonify({"error": "Cannot delete system categories"}), 403
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"deleted": cat_id})
