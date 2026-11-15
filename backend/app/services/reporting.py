import csv
import io
import zipfile
from math import cos, pi, sin
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.analytics import DISCLAIMER


def _spreadsheet_safe(value: object) -> str:
    text = str(value if value is not None else "")
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def build_csv_bundle(report: dict) -> bytes:
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        def write_csv(filename: str, headers: list[str], rows: list[list[object]]) -> None:
            output = io.StringIO(newline="")
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows([[_spreadsheet_safe(value) for value in row] for row in rows])
            archive.writestr(filename, "\ufeff" + output.getvalue())

        summary = report["network_summary"]
        write_csv("summary.csv", ["field", "value"], [
            ["investigation_reference", report["reference_id"]],
            ["title", report["title"]],
            ["created_at_utc", report["created_at"]],
            ["selected_entity_ids", ";".join(report["selected_entities"]) or "All synthetic entities"],
            ["entities_in_scope", summary["entity_count"]],
            ["relationships_in_scope", summary["relationship_count"]],
            ["connected_components", summary["component_count"]],
            ["network_density", summary["density"]],
            ["anomaly_finding_count", len(report["anomaly_findings"])],
            ["anomaly_method", report.get("anomaly_method", "Isolation Forest + DBSCAN")],
            ["anomaly_sample_count", report.get("anomaly_sample_count", "")],
            ["anomaly_contamination", report.get("anomaly_contamination", "")],
            ["anomaly_features", ";".join(report.get("anomaly_features", []))],
            ["disclaimer", report["disclaimer"]],
        ])

        write_csv("anomaly_findings.csv", [
            "transaction_id", "source_entity_id", "target_entity_id", "amount", "currency",
            "outlier_score", "confidence", "isolation_forest_signal", "dbscan_signal",
            "explanation", "limitations",
        ], [[
            item["transaction_id"],
            *(item.get("entity_ids", ["", ""]) + ["", ""])[:2],
            item.get("amount", ""),
            item.get("currency", ""),
            item.get("score", ""),
            item.get("confidence", ""),
            item.get("signals", {}).get("isolation_forest", ""),
            item.get("signals", {}).get("dbscan", ""),
            item.get("explanation", ""),
            item.get("limitations", report["disclaimer"]),
        ] for item in report["anomaly_findings"]])

        write_csv("entities.csv", ["entity_id", "label", "entity_type"], [[
            node["id"], node.get("label", ""), node.get("entity_type", "")
        ] for node in report.get("network_graph", {}).get("nodes", [])])

        write_csv("relationships.csv", [
            "source_entity_id", "target_entity_id", "relationship_type", "weight",
        ], [[
            edge["source"], edge["target"], edge.get("type", ""), edge.get("weight", "")
        ] for edge in report.get("network_graph", {}).get("edges", [])])

        archive.writestr("README.txt", (
            "Signal Atlas synthetic network analysis export\n"
            "All records in this archive are fictional synthetic data.\n"
            f"{report['disclaimer']}\n"
            "Files: summary.csv, anomaly_findings.csv, entities.csv, relationships.csv.\n"
        ))
    return bundle.getvalue()


def build_pdf_report(report: dict) -> bytes:
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=22, leading=27, textColor=colors.HexColor("#122538"),
                              alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name="Subtle", parent=styles["Normal"], fontSize=9, leading=13,
                              textColor=colors.HexColor("#5F6F82")))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
                              fontSize=13, leading=17, textColor=colors.HexColor("#173A4B"),
                              spaceBefore=12, spaceAfter=7))
    styles.add(ParagraphStyle(name="TableBody", parent=styles["BodyText"], fontSize=7.4, leading=10,
                              textColor=colors.HexColor("#273548")))
    styles.add(ParagraphStyle(name="TableSmall", parent=styles["BodyText"], fontSize=6.7, leading=8.5,
                              textColor=colors.HexColor("#344256")))
    styles.add(ParagraphStyle(name="Disclaimer", parent=styles["BodyText"], fontSize=8, leading=11,
                              textColor=colors.HexColor("#72551A")))
    styles.add(ParagraphStyle(name="GraphLabel", parent=styles["BodyText"], fontSize=7, leading=8,
                              alignment=TA_CENTER, textColor=colors.HexColor("#273548")))

    doc = SimpleDocTemplate(
        output, pagesize=letter, rightMargin=0.56 * inch, leftMargin=0.56 * inch,
        topMargin=0.72 * inch, bottomMargin=0.63 * inch, title=report["title"],
        author="Signal Atlas - Synthetic Network Analysis",
    )

    def page_chrome(canvas, document) -> None:
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7E1E9"))
        canvas.line(doc.leftMargin, letter[1] - 0.48 * inch, letter[0] - doc.rightMargin, letter[1] - 0.48 * inch)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.HexColor("#1B5966"))
        canvas.drawString(doc.leftMargin, letter[1] - 0.36 * inch, "SIGNAL ATLAS  /  FICTIONAL DATA")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#667588"))
        canvas.drawRightString(letter[0] - doc.rightMargin, letter[1] - 0.36 * inch, report["reference_id"])
        canvas.line(doc.leftMargin, 0.43 * inch, letter[0] - doc.rightMargin, 0.43 * inch)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(doc.leftMargin, 0.29 * inch, "Exploratory analysis only - not evidence or a determination of culpability.")
        canvas.drawRightString(letter[0] - doc.rightMargin, 0.29 * inch, f"Page {document.page}")
        canvas.restoreState()

    story = [
        Spacer(1, 0.1 * inch),
        Paragraph(escape(report["title"]), styles["CoverTitle"]),
        Paragraph(f"Investigation reference <b>{escape(report['reference_id'])}</b>  |  "
                  f"Generated {escape(report['created_at'])}", styles["Subtle"]),
        Spacer(1, 0.16 * inch),
        Paragraph("Executive summary", styles["SectionTitle"]),
    ]
    summary = report["network_summary"]
    kpis = [
        ["ENTITIES", "RELATIONSHIPS", "COMPONENTS", "DENSITY", "ANOMALY LEADS"],
        [str(summary["entity_count"]), str(summary["relationship_count"]),
         str(summary["component_count"]), f"{summary['density']:.3f}",
         str(len(report["anomaly_findings"]))],
    ]
    kpi_table = Table(kpis, colWidths=[1.05 * inch, 1.16 * inch, 1.12 * inch, 0.9 * inch, 1.38 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F7F9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#537080")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#143B4B")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 6.6),
        ("FONTSIZE", (0, 1), (-1, 1), 15),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E4EA")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E4EA")),
    ]))
    story.extend([
        kpi_table,
        Spacer(1, 0.1 * inch),
        Paragraph(f"<b>Scope:</b> {escape(', '.join(report['selected_entities']) or 'All synthetic entities')}",
                  styles["Subtle"]),
        Paragraph(f"<b>Detection methods:</b> {escape(report.get('anomaly_method', 'Isolation Forest + DBSCAN'))}",
                  styles["Subtle"]),
        Paragraph(f"<b>Feature fields:</b> {escape(', '.join(report.get('anomaly_features', ['transaction amount', 'endpoint activity count'])))}",
                  styles["Subtle"]),
        Paragraph(f"<b>Sample size / contamination setting:</b> "
                  f"{report.get('anomaly_sample_count', len(report['anomaly_findings']))} transactions / "
                  f"{report.get('anomaly_contamination', 0.05):.0%}", styles["Subtle"]),
        Paragraph("Interpretation and limitations", styles["SectionTitle"]),
        Paragraph(escape(report["disclaimer"]), styles["Disclaimer"]),
        Paragraph("Anomaly findings are transaction-level statistical outliers in a small synthetic sample. "
                  "Scores are relative to the analyzed sample; they are not probabilities, causal explanations, "
                  "or person-level risk scores. Review the underlying records and ordinary explanations independently.",
                  styles["Subtle"]),
        Paragraph(f"Detailed anomaly findings ({len(report['anomaly_findings'])})", styles["SectionTitle"]),
    ])

    detail_style = styles["TableSmall"]
    table_data = [[
        Paragraph("<b>Transaction</b>", detail_style),
        Paragraph("<b>Entities / amount</b>", detail_style),
        Paragraph("<b>Score / signal</b>", detail_style),
        Paragraph("<b>Pattern explanation and limitations</b>", detail_style),
    ]]
    for item in report["anomaly_findings"]:
        entity_ids = item.get("entity_ids", [])
        signals = item.get("signals", {})
        signal_text = ", ".join(
            name.replace("_", " ") for name, enabled in signals.items() if enabled
        ) or item.get("confidence", "exploratory")
        description = (
            f"<b>{escape(item.get('explanation', 'No explanation supplied.'))}</b><br/>"
            f"<font color='#69778A'>{escape(item.get('limitations', report['disclaimer']))}</font>"
        )
        table_data.append([
            Paragraph(escape(item.get("transaction_id", "")), detail_style),
            Paragraph(f"{escape(', '.join(entity_ids))}<br/>"
                      f"{escape(str(item.get('amount', '')))} {escape(item.get('currency', ''))}", detail_style),
            Paragraph(f"{item.get('score', 0):.3f}<br/>{escape(signal_text)}", detail_style),
            Paragraph(description, detail_style),
        ])
    findings_table = LongTable(
        table_data, colWidths=[0.85 * inch, 1.3 * inch, 1.1 * inch, 4.0 * inch],
        repeatRows=1, splitByRow=1, hAlign="LEFT",
    )
    findings_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF1F5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#163F50")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FB")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E1E8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    if report["anomaly_findings"]:
        story.append(findings_table)
    else:
        story.append(Paragraph("No anomaly findings were returned for this analysis run.", styles["Subtle"]))

    graph_data = report.get("network_graph", {})
    graph_nodes = graph_data.get("nodes", [])
    graph_edges = graph_data.get("edges", [])
    story.extend([
        PageBreak(),
        Paragraph("Network visualization", styles["SectionTitle"]),
        Paragraph("Two-dimensional overview of the report scope. Layout is illustrative; edges show recorded synthetic associations.",
                  styles["Subtle"]),
        Spacer(1, 0.12 * inch),
    ])
    graph_width, graph_height = 7.35 * inch, 6.55 * inch
    if graph_nodes:
        node_positions = {}
        center_x, center_y = graph_width / 2, graph_height / 2
        radius = min(graph_width, graph_height) * 0.38
        for index, node in enumerate(graph_nodes):
            angle = 2 * pi * index / max(len(graph_nodes), 1) - pi / 2
            node_positions[node["id"]] = (center_x + radius * cos(angle), center_y + radius * sin(angle))
        from reportlab.graphics.shapes import Circle, Drawing, Line, String
        drawing = Drawing(graph_width, graph_height)
        type_colors = {
            "person": colors.HexColor("#1EA9BA"),
            "organization": colors.HexColor("#8B65C6"),
            "phone": colors.HexColor("#5276D1"),
            "location": colors.HexColor("#309D78"),
        }
        for edge in graph_edges:
            if edge["source"] in node_positions and edge["target"] in node_positions:
                x1, y1 = node_positions[edge["source"]]
                x2, y2 = node_positions[edge["target"]]
                drawing.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#BBC7D1"), strokeWidth=0.65))
        for node in graph_nodes:
            x, y = node_positions[node["id"]]
            dot_color = type_colors.get(node.get("entity_type"), colors.HexColor("#65758A"))
            drawing.add(Circle(x, y, 4.8, fillColor=dot_color, strokeColor=colors.white, strokeWidth=0.8))
            label = node.get("label", node["id"])
            if len(label) > 24:
                label = label[:21] + "..."
            drawing.add(String(x, y - 11, label, fontName="Helvetica", fontSize=5.8,
                               textAnchor="middle", fillColor=colors.HexColor("#28384B")))
        story.append(drawing)
    else:
        story.append(Paragraph("No entities are in the selected graph scope.", styles["Subtle"]))

    legend = Table([[
        Paragraph("<font color='#1EA9BA'>●</font> Person", styles["GraphLabel"]),
        Paragraph("<font color='#8B65C6'>●</font> Organization", styles["GraphLabel"]),
        Paragraph("<font color='#5276D1'>●</font> Phone", styles["GraphLabel"]),
        Paragraph("<font color='#309D78'>●</font> Location", styles["GraphLabel"]),
    ]], colWidths=[1.65 * inch] * 4)
    legend.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(legend)
    story.append(Paragraph(f"{len(graph_nodes)} entities · {len(graph_edges)} relationships in the visualization.",
                           ParagraphStyle("GraphCaption", parent=styles["Subtle"], alignment=TA_CENTER, spaceBefore=7)))

    doc.build(story, onFirstPage=page_chrome, onLaterPages=page_chrome)
    return output.getvalue()
