"""PDF invoice for an order: GET /order/<id>/invoice.pdf (owner, admin, or a seller whose product is in the order)."""
import io
from datetime import datetime
from flask import Blueprint, abort, send_file, current_app
from backend import query, current_user, login_required

bp = Blueprint("invoice", __name__)


def _allowed(o, user):
    if o["user_id"] == user["id"] or user["role"] == "admin":
        return True
    if user["role"] == "seller":
        return bool(query("""SELECT 1 FROM order_items oi JOIN products p ON p.id=oi.product_id JOIN sellers s ON s.id=p.seller_id
                             WHERE oi.order_id=? AND s.user_id=?""", (o["id"], user["id"]), one=True))
    return False


def breakdown(o, items):
    cfg = current_app.config
    net = sum(i["price"] * i["quantity"] for i in items)
    delivery = 0 if (net == 0 or net >= cfg["FREE_DELIVERY_ABOVE"]) else cfg["DELIVERY_FEE"]
    tax = round(net * cfg["TAX_PERCENT"] / 100)
    ex = query("SELECT * FROM order_extras WHERE order_id=?", (o["id"],), one=True)
    coupon = ex["coupon_discount"] if ex else 0
    return dict(net=net, delivery=delivery, tax=tax, coupon=coupon, code=ex["coupon_code"] if ex else None,
                total=o["total_amount"], computed=net + delivery + tax - coupon)


@bp.route("/order/<int:oid>/invoice.pdf")
@login_required
def invoice_pdf(oid):
    user = current_user()
    o = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
    if not o or not _allowed(o, user):
        abort(404)
    items = query("SELECT * FROM order_items WHERE order_id=?", (oid,))
    sellers = query("""SELECT DISTINCT s.business_name, s.location FROM order_items oi JOIN products p ON p.id=oi.product_id
                       JOIN sellers s ON s.id=p.seller_id WHERE oi.order_id=?""", (oid,))
    pay = query("SELECT * FROM payments WHERE order_id=?", (oid,), one=True)
    b = breakdown(o, items)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    except ImportError:
        abort(503, "PDF support is not installed. Run: pip install reportlab")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                            title=f"Invoice {o['order_number']}", author="AgroConnect")
    ss = getSampleStyleSheet()
    green, dark = colors.HexColor("#168A3A"), colors.HexColor("#0B120D")
    h = ParagraphStyle("h", parent=ss["Title"], textColor=green, fontSize=22, alignment=0, spaceAfter=0)
    small = ParagraphStyle("s", parent=ss["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#444444"))
    norm = ParagraphStyle("n", parent=ss["Normal"], fontSize=10, leading=13)
    bold = ParagraphStyle("b", parent=norm, fontName="Helvetica-Bold")
    rs = lambda n: f"Rs. {n:,.2f}"          # the built-in PDF fonts have no rupee glyph
    try:
        date = datetime.fromisoformat(o["created_at"]).strftime("%d %b %Y")
    except Exception:
        date = str(o["created_at"])[:10]
    esc = lambda t: str(t or "").replace("&", "&amp;").replace("<", "&lt;")

    story = [Paragraph("AgroConnect", h), Paragraph("Tax Invoice", ParagraphStyle("t", parent=norm, textColor=colors.grey)), Spacer(1, 8)]
    meta = Table([
        [Paragraph(f"<b>Invoice for order</b><br/>{esc(o['order_number'])}", norm), Paragraph(f"<b>Date</b><br/>{date}", norm),
         Paragraph(f"<b>Payment</b><br/>{esc(o['payment_method'])}" + (f" ({esc(pay['status'])})" if pay else ""), norm)],
    ], colWidths=[70 * mm, 40 * mm, 66 * mm])
    meta.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cfd8d2")), ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e1e7e3")),
                              ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [meta, Spacer(1, 10)]
    party = Table([[Paragraph("<b>Sold by</b><br/>" + "<br/>".join(f"{esc(s['business_name'])}, {esc(s['location'])}" for s in sellers) or "AgroConnect", norm),
                    Paragraph(f"<b>Billed &amp; shipped to</b><br/>{esc(o['customer_name'])}<br/>{esc(o['phone'])}<br/>{esc(o['shipping_address'])}", norm)]],
                  colWidths=[88 * mm, 88 * mm])
    party.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [party, Spacer(1, 12)]

    rows = [["#", "Item", "Qty", "Unit price", "Amount"]]
    for n, i in enumerate(items, 1):
        rows.append([str(n), Paragraph(esc(i["name"]), norm), str(i["quantity"]), rs(i["price"]), rs(i["price"] * i["quantity"])])
    t = Table(rows, colWidths=[10 * mm, 86 * mm, 16 * mm, 32 * mm, 32 * mm], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), dark), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                           ("FONTSIZE", (0, 0), (-1, -1), 9.5), ("ALIGN", (2, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f8f5")]),
                           ("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.HexColor("#cfd8d2")), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [t, Spacer(1, 10)]

    tr = [["Items total (after discounts)", rs(b["net"])], ["Delivery", "Free" if not b["delivery"] else rs(b["delivery"])], [f"GST ({current_app.config['TAX_PERCENT']}%)", rs(b["tax"])]]
    if b["coupon"]:
        tr.append([f"Coupon {b['code']}", "- " + rs(b["coupon"])])
    tr.append(["Total paid / payable", rs(b["total"])])
    tt = Table(tr, colWidths=[56 * mm, 36 * mm], hAlign="RIGHT")
    tt.setStyle(TableStyle([("ALIGN", (1, 0), (1, -1), "RIGHT"), ("FONTSIZE", (0, 0), (-1, -1), 10), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                            ("LINEABOVE", (0, -1), (-1, -1), 0.8, green), ("TEXTCOLOR", (0, -1), (-1, -1), green), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
    story += [tt, Spacer(1, 18),
              Paragraph("This is a computer-generated invoice and needs no signature. GST is calculated on the item value before any coupon. "
                        "Demo marketplace: payments are simulated.", small)]
    doc.build(story)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=f"Invoice-{o['order_number']}.pdf")
