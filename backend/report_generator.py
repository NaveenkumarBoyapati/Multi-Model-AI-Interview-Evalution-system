"""
PDF Report Generator for Multi-Model AI Interview Evaluation System.
Generates structured, professional server-side PDF evaluation reports
for completed and terminated interviews using ReportLab.
"""

import io
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that computes total page count dynamically
    and draws professional running footers (Page X of Y).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_decorations(self, total_pages: int):
        self.saveState()
        page_width, _ = letter

        # Running Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(40, 42, page_width - 40, 42)

        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(40, 28, "Multi-model AI Interview Evaluation System")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.drawRightString(page_width - 40, 28, page_str)

        self.restoreState()


def _format_datetime(dt_val: Any) -> str:
    """Formats datetime object or ISO string to readable string."""
    if not dt_val:
        return "Not available"
    if isinstance(dt_val, str):
        try:
            dt_val = datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
        except Exception:
            return dt_val
    if isinstance(dt_val, datetime):
        return dt_val.strftime("%d %B %Y, %I:%M %p")
    return str(dt_val)


def _format_duration(dur_val: Any) -> str:
    """Formats duration seconds into minutes and seconds."""
    if dur_val is None or dur_val == "":
        return "Not recorded"
    try:
        total_sec = float(dur_val)
        mins = int(total_sec // 60)
        secs = int(total_sec % 60)
        if mins > 0:
            return f"{mins} min {secs} sec ({total_sec:.1f}s)"
        return f"{total_sec:.1f} seconds"
    except Exception:
        return str(dur_val)


def _parse_list(val: Any) -> List[str]:
    """Safely parses JSON lists or string lists into python list of strings."""
    if not val:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, str):
        val_str = val.strip()
        if val_str.startswith("[") and val_str.endswith("]"):
            try:
                parsed = json.loads(val_str)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        # Fallback comma-separated
        return [x.strip() for x in val_str.split(",") if x.strip()]
    return [str(val)]


def _get_performance_level(overall_score: Optional[float]) -> str:
    """Classifies overall score using existing system thresholds."""
    if overall_score is None:
        return "Not Available"
    val = round(float(overall_score), 1)
    if val >= 80:
        return "Excellent"
    elif val >= 65:
        return "Good"
    elif val >= 50:
        return "Average"
    else:
        return "Needs Improvement"


def generate_interview_report_pdf(
    interview_data: Dict[str, Any],
    candidate_user: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Compiles full interview results into a professional multi-page PDF buffer.
    Adheres strictly to completed vs terminated interview rules.
    Read-only presentation: does NOT mutate database or run AI models.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=36,
        bottomMargin=52,
    )

    content_width = letter[0] - 80  # 532 pt

    # Base Styles
    styles = getSampleStyleSheet()

    # Custom Typography Palette
    c_primary = colors.HexColor("#1e3a8a")     # Deep Navy
    c_accent = colors.HexColor("#2563eb")      # Brand Blue
    c_text = colors.HexColor("#0f172a")        # Dark Slate
    c_muted = colors.HexColor("#64748b")       # Cool Gray
    c_bg_light = colors.HexColor("#f8fafc")    # Light Slate
    c_border = colors.HexColor("#e2e8f0")      # Border Slate
    c_green = colors.HexColor("#15803d")       # Success Green
    c_red = colors.HexColor("#b91c1c")         # Danger Red

    styles.add(ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=c_primary,
        alignment=0,
    ))

    styles.add(ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_accent,
        alignment=0,
    ))

    styles.add(ParagraphStyle(
        "HeaderMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=c_muted,
        alignment=2,
    ))

    styles.add(ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=c_primary,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "SubSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13.5,
        textColor=c_text,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=c_text,
    ))

    styles.add(ParagraphStyle(
        "ReportBodyMuted",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=c_muted,
    ))

    styles.add(ParagraphStyle(
        "ReportBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=c_text,
    ))

    styles.add(ParagraphStyle(
        "AnswerBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#1e293b"),
    ))

    styles.add(ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        leftIndent=12,
        firstLineIndent=-8,
    ))

    styles.add(ParagraphStyle(
        "ScoreHeroBig",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=c_accent,
        alignment=1,
    ))

    styles.add(ParagraphStyle(
        "ScoreHeroLevel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=c_primary,
        alignment=1,
    ))

    # Extract interview records
    interview = interview_data.get("interview", {}) or {}
    answers = interview_data.get("answers", []) or []
    evaluation = interview_data.get("evaluation")
    feedback = interview_data.get("feedback")
    recording_available = bool(interview_data.get("recording_available", False))

    cand_user = candidate_user or {}
    cand_name = cand_user.get("name") or "Interview Candidate"
    cand_email = cand_user.get("email") or "Not provided"

    int_id = interview.get("id") or "N/A"
    # Role must come from the interview record itself
    int_role = interview.get("role") or "General Role"
    int_date_formatted = _format_datetime(interview.get("created_at"))
    int_duration_formatted = _format_duration(interview.get("duration_seconds"))

    raw_status = str(interview.get("status", "")).strip()
    is_terminated = raw_status.lower() == "terminated"

    story = []

    # ==================================================
    # 4. PDF HEADER
    # ==================================================
    header_left = [
        Paragraph("MULTI-MODEL AI INTERVIEW EVALUATION SYSTEM", styles["HeaderTitle"]),
        Spacer(1, 2),
        Paragraph("Interview Evaluation Report", styles["HeaderSubtitle"]),
    ]
    header_right = [
        Paragraph(f"<b>Interview ID:</b> #{int_id}", styles["HeaderMeta"]),
        Paragraph(f"<b>Date:</b> {int_date_formatted}", styles["HeaderMeta"]),
        Paragraph(f"<b>Role:</b> {int_role}", styles["HeaderMeta"]),
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[content_width * 0.62, content_width * 0.38]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=4, spaceAfter=10))

    # ==================================================
    # 5. CANDIDATE INFORMATION & 6. INTERVIEW STATUS
    # ==================================================
    story.append(Paragraph("Candidate & Interview Information", styles["SectionHeading"]))
    story.append(Spacer(1, 4))

    if is_terminated:
        status_display = "TERMINATED"
        status_color = c_red
        sec_violation_display = "Yes"
        tab_switch_count = interview.get("tab_switch_count", 1) or 1
        term_reason = interview.get("terminated_reason") or "Tab Switch Detected"
    else:
        status_display = "COMPLETED"
        status_color = c_green
        sec_violation_display = "No"
        tab_switch_count = interview.get("tab_switch_count", 0) or 0
        term_reason = "None"

    # 2-column key-value grid
    info_data = [
        [
            Paragraph("<b>Full Name:</b>", styles["ReportBody"]),
            Paragraph(cand_name, styles["ReportBody"]),
            Paragraph("<b>Interview ID:</b>", styles["ReportBody"]),
            Paragraph(f"#{int_id}", styles["ReportBody"]),
        ],
        [
            Paragraph("<b>Email:</b>", styles["ReportBody"]),
            Paragraph(cand_email, styles["ReportBody"]),
            Paragraph("<b>Interview Role:</b>", styles["ReportBody"]),
            Paragraph(int_role, styles["ReportBodyBold"]),
        ],
        [
            Paragraph("<b>Interview Date:</b>", styles["ReportBody"]),
            Paragraph(int_date_formatted, styles["ReportBody"]),
            Paragraph("<b>Interview Duration:</b>", styles["ReportBody"]),
            Paragraph(int_duration_formatted, styles["ReportBody"]),
        ],
        [
            Paragraph("<b>Interview Status:</b>", styles["ReportBody"]),
            Paragraph(f"<font color='{status_color.hexval()}'><b>{status_display}</b></font>", styles["ReportBody"]),
            Paragraph("<b>Security Violation:</b>", styles["ReportBody"]),
            Paragraph(
                f"<font color='{c_red.hexval() if sec_violation_display == 'Yes' else c_green.hexval()}'><b>{sec_violation_display}</b></font>",
                styles["ReportBody"]
            ),
        ],
        [
            Paragraph("<b>Tab Switch Count:</b>", styles["ReportBody"]),
            Paragraph(str(tab_switch_count), styles["ReportBody"]),
            Paragraph("<b>Interview Recording:</b>", styles["ReportBody"]),
            Paragraph("Available" if recording_available else "Unavailable", styles["ReportBody"]),
        ],
    ]

    if is_terminated:
        info_data.append([
            Paragraph("<b>Termination Reason:</b>", styles["ReportBody"]),
            Paragraph(f"<font color='{c_red.hexval()}'><b>{term_reason}</b></font>", styles["ReportBody"]),
            Paragraph("", styles["ReportBody"]),
            Paragraph("", styles["ReportBody"]),
        ])

    info_table = Table(
        info_data,
        colWidths=[content_width * 0.22, content_width * 0.32, content_width * 0.22, content_width * 0.24]
    )
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
        ("BOX", (0, 0), (-1, -1), 0.75, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ==================================================
    # 15. TERMINATED INTERVIEW PRESENTATION
    # ==================================================
    if is_terminated:
        term_banner_data = [
            [
                Paragraph("<b>SECURITY NOTICE: INTERVIEW TERMINATED</b>", ParagraphStyle(
                    "TermTitle",
                    parent=styles["Normal"],
                    fontName="Helvetica-Bold",
                    fontSize=11.5,
                    leading=15.5,
                    textColor=c_red,
                ))
            ],
            [
                Paragraph(
                    "<b>Reason:</b> This interview was automatically terminated because a tab switch was detected. "
                    "AI evaluation was not generated.",
                    ParagraphStyle(
                        "TermBody",
                        parent=styles["Normal"],
                        fontName="Helvetica",
                        fontSize=9,
                        leading=13.5,
                        textColor=colors.HexColor("#7f1d1d"),
                    )
                )
            ],
            [
                Paragraph(
                    f"<b>Status:</b> Terminated &nbsp;|&nbsp; <b>Termination Reason:</b> {term_reason} &nbsp;|&nbsp; "
                    f"<b>Security Violation:</b> Yes &nbsp;|&nbsp; <b>Tab Switch Count:</b> {tab_switch_count} &nbsp;|&nbsp; "
                    f"<b>Recording:</b> {'Available' if recording_available else 'Unavailable'} &nbsp;|&nbsp; "
                    f"<b>AI Evaluation:</b> Not Generated",
                    ParagraphStyle(
                        "TermDetails",
                        parent=styles["Normal"],
                        fontName="Helvetica-Bold",
                        fontSize=8.5,
                        leading=12.5,
                        textColor=c_red,
                    )
                )
            ]
        ]
        term_table = Table(term_banner_data, colWidths=[content_width])
        term_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f87171")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(term_table)
        story.append(Spacer(1, 10))

        # Transcript section for terminated interview if available
        transcript_text = (interview.get("transcript") or "").strip()
        if transcript_text:
            story.append(Paragraph("Speech Transcription Prior to Termination", styles["SectionHeading"]))
            story.append(Spacer(1, 3))
            trans_table = Table([[Paragraph(transcript_text, styles["AnswerBody"])]], colWidths=[content_width])
            trans_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(trans_table)
            story.append(Spacer(1, 4))
            story.append(Paragraph("<i>Speech transcription generated by Faster-Whisper.</i>", styles["ReportBodyMuted"]))
            story.append(Spacer(1, 10))

        # Recording note
        story.append(Paragraph("Recording Information", styles["SectionHeading"]))
        story.append(Spacer(1, 3))
        rec_msg = (
            "Session recording captured and stored securely in system storage."
            if recording_available
            else "No session recording available for this interview."
        )
        rec_table = Table([[
            Paragraph(f"<b>Recording Status:</b> {'Available' if recording_available else 'Unavailable'}<br/>{rec_msg}", styles["ReportBody"])
        ]], colWidths=[content_width])
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(rec_table)

        doc.build(story, canvasmaker=NumberedCanvas)
        return buffer.getvalue()

    # ==================================================
    # 7. COMPLETED INTERVIEW — OVERALL PERFORMANCE
    # ==================================================
    raw_overall = (
        evaluation.get("overall_score")
        if (evaluation and evaluation.get("overall_score") is not None)
        else interview.get("overall_score")
    )
    overall_val = round(float(raw_overall), 1) if raw_overall is not None else None
    overall_level = _get_performance_level(overall_val)

    # Score Card
    score_left = [
        Paragraph(f"<b>{overall_val:.1f}</b> <font size=11 color='#64748b'>/ 100</font>" if overall_val is not None else "-- / 100", styles["ScoreHeroBig"]),
        Spacer(1, 2),
        Paragraph(f"Performance: <b>{overall_level}</b>", styles["ScoreHeroLevel"]),
    ]

    eval_summary = ""
    if feedback and feedback.get("overall_performance"):
        eval_summary = feedback["overall_performance"]
    elif feedback and feedback.get("summary"):
        eval_summary = feedback["summary"]
    else:
        eval_summary = f"Completed mock interview for the {int_role} role. Evaluated {len(answers)} question responses."

    score_right = [
        Paragraph("<b>Performance Overview</b>", styles["SubSectionHeading"]),
        Spacer(1, 2),
        Paragraph(eval_summary, styles["ReportBody"]),
    ]

    perf_card = Table(
        [[score_left, score_right]],
        colWidths=[content_width * 0.30, content_width * 0.70]
    )
    perf_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#eff6ff")),
        ("BACKGROUND", (1, 0), (1, 0), c_bg_light),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#bfdbfe")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bfdbfe")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(Paragraph("Overall Performance", styles["SectionHeading"]))
    story.append(Spacer(1, 4))
    story.append(perf_card)
    story.append(Spacer(1, 10))

    # ==================================================
    # 8. SCORE BREAKDOWN
    # ==================================================
    story.append(Paragraph("Score Breakdown", styles["SectionHeading"]))
    story.append(Spacer(1, 4))

    def _fmt_pct(val: Any) -> str:
        if val is None or val == "":
            return "Not Available"
        try:
            return f"{float(val):.1f}%"
        except Exception:
            return str(val)

    # Resolve category scores from evaluation / interview
    tech_score = evaluation.get("technical_score") if evaluation else interview.get("technical_score")
    rel_score = evaluation.get("relevance_score") if evaluation else interview.get("relevance_score")
    comm_score = evaluation.get("communication_score") if evaluation else interview.get("communication_score")
    conf_score = evaluation.get("confidence_score") if evaluation else interview.get("confidence_score")
    prob_score = evaluation.get("problem_solving_score") if evaluation else interview.get("problem_solving_score")

    # Average concept coverage and completeness from answers if not directly in evaluation
    concept_scores_list = [
        a.get("concept_coverage_score")
        for a in answers
        if a.get("concept_coverage_score") is not None
    ]
    if not concept_scores_list:
        concept_scores_list = [
            a.get("concept_score")
            for a in answers
            if a.get("concept_score") is not None
        ]
    avg_concept = (
        round(sum(float(x) for x in concept_scores_list) / len(concept_scores_list), 1)
        if concept_scores_list
        else None
    )

    comp_scores_list = [
        a.get("completeness_score")
        for a in answers
        if a.get("completeness_score") is not None
    ]
    avg_comp = (
        round(sum(float(x) for x in comp_scores_list) / len(comp_scores_list), 1)
        if comp_scores_list
        else None
    )

    breakdown_data = [
        [Paragraph("<b>Category</b>", styles["ReportBodyBold"]), Paragraph("<b>Score</b>", styles["ReportBodyBold"]),
         Paragraph("<b>Category</b>", styles["ReportBodyBold"]), Paragraph("<b>Score</b>", styles["ReportBodyBold"])],
        [
            Paragraph("Technical Knowledge", styles["ReportBody"]), Paragraph(_fmt_pct(tech_score), styles["ReportBodyBold"]),
            Paragraph("Communication", styles["ReportBody"]), Paragraph(_fmt_pct(comm_score), styles["ReportBodyBold"]),
        ],
        [
            Paragraph("Question Relevance", styles["ReportBody"]), Paragraph(_fmt_pct(rel_score), styles["ReportBodyBold"]),
            Paragraph("Confidence", styles["ReportBody"]), Paragraph(_fmt_pct(conf_score), styles["ReportBodyBold"]),
        ],
        [
            Paragraph("Concept Coverage", styles["ReportBody"]), Paragraph(_fmt_pct(avg_concept), styles["ReportBodyBold"]),
            Paragraph("Problem Solving", styles["ReportBody"]), Paragraph(_fmt_pct(prob_score), styles["ReportBodyBold"]),
        ],
        [
            Paragraph("Completeness", styles["ReportBody"]), Paragraph(_fmt_pct(avg_comp), styles["ReportBodyBold"]),
            Paragraph("Overall Score", styles["ReportBodyBold"]), Paragraph(f"<font color='{c_accent.hexval()}'><b>{_fmt_pct(overall_val)}</b></font>", styles["ReportBodyBold"]),
        ],
    ]

    breakdown_table = Table(
        breakdown_data,
        colWidths=[content_width * 0.32, content_width * 0.18, content_width * 0.32, content_width * 0.18]
    )
    breakdown_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("BOX", (0, 0), (-1, -1), 0.75, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 10))

    # ==================================================
    # 9. QUESTION-WISE EVALUATION
    # ==================================================
    if answers:
        for idx, ans in enumerate(answers, start=1):
            q_num = ans.get("question_number") or idx
            q_text = ans.get("question_text") or f"Question {q_num}"
            ans_text = (ans.get("answer_text") or "").strip()
            if not ans_text:
                ans_text = "<i>No verbal response recorded for this question.</i>"

            exp_concepts = _parse_list(ans.get("expected_concepts"))
            matched_concepts = _parse_list(ans.get("matched_concepts"))
            missing_concepts = _parse_list(ans.get("missing_concepts"))

            ans_tech = ans.get("technical_score")
            ans_rel = ans.get("relevance_score")
            ans_concept = ans.get("concept_coverage_score") if ans.get("concept_coverage_score") is not None else ans.get("concept_score")
            ans_comp = ans.get("completeness_score")
            ans_comm = ans.get("communication_score")
            ans_conf = ans.get("confidence_score")
            ans_prob = ans.get("problem_solving_score")
            ans_overall = ans.get("overall_answer_score")

            q_elements = []

            # If it's the first question, include the Section Heading inside the card block so it never separates
            if idx == 1:
                q_elements.append(Paragraph("Question-Wise Evaluation", styles["SectionHeading"]))
                q_elements.append(Spacer(1, 4))

            # Question Header Card
            q_header_text = f"<b>Question {q_num}:</b> {q_text}"
            q_elements.append(Paragraph(q_header_text, styles["SubSectionHeading"]))
            q_elements.append(Spacer(1, 3))

            # Candidate Answer box
            ans_box = Table(
                [[
                    Paragraph("<b>Candidate Response:</b>", styles["ReportBodyBold"]),
                ], [
                    Paragraph(ans_text, styles["AnswerBody"]),
                ]],
                colWidths=[content_width - 16]
            )
            ans_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            q_elements.append(ans_box)
            q_elements.append(Spacer(1, 4))

            # Concept Breakdown Table
            exp_str = ", ".join(exp_concepts) if exp_concepts else "None specified"
            matched_str = ", ".join(matched_concepts) if matched_concepts else "None identified"
            missing_str = ", ".join(missing_concepts) if missing_concepts else "None"

            concept_grid = [
                [Paragraph("<b>Expected Concepts:</b>", styles["ReportBodyBold"]), Paragraph(exp_str, styles["ReportBody"])],
                [Paragraph("<b>Matched Concepts:</b>", styles["ReportBodyBold"]), Paragraph(f"<font color='{c_green.hexval()}'><b>{matched_str}</b></font>", styles["ReportBody"])],
                [Paragraph("<b>Missing Concepts:</b>", styles["ReportBodyBold"]), Paragraph(f"<font color='{c_red.hexval()}'><b>{missing_str}</b></font>", styles["ReportBody"])],
            ]
            concept_table = Table(concept_grid, colWidths=[110, content_width - 16 - 110])
            concept_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            q_elements.append(concept_table)
            q_elements.append(Spacer(1, 4))

            # Question Score Grid: Clean 4 columns x 2 rows (fits comfortably without wrapping words)
            q_score_data = [
                [
                    Paragraph("<b>Technical:</b> " + _fmt_pct(ans_tech), styles["ReportBody"]),
                    Paragraph("<b>Relevance:</b> " + _fmt_pct(ans_rel), styles["ReportBody"]),
                    Paragraph("<b>Concept Cov:</b> " + _fmt_pct(ans_concept), styles["ReportBody"]),
                    Paragraph("<b>Completeness:</b> " + _fmt_pct(ans_comp), styles["ReportBody"]),
                ],
                [
                    Paragraph("<b>Communication:</b> " + _fmt_pct(ans_comm), styles["ReportBody"]),
                    Paragraph("<b>Confidence:</b> " + _fmt_pct(ans_conf), styles["ReportBody"]),
                    Paragraph("<b>Problem Solving:</b> " + _fmt_pct(ans_prob), styles["ReportBody"]),
                    Paragraph(f"<b>Overall:</b> <font color='{c_accent.hexval()}'><b>{_fmt_pct(ans_overall)}</b></font>", styles["ReportBodyBold"]),
                ]
            ]
            col_w_4 = (content_width - 16) / 4.0
            q_score_table = Table(q_score_data, colWidths=[col_w_4] * 4)
            q_score_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BACKGROUND", (3, 1), (3, 1), colors.HexColor("#eff6ff")),
                ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            q_elements.append(q_score_table)
            q_elements.append(Spacer(1, 4))

            # 10. Question Strengths & 11. Question Improvements
            q_strengths = _parse_list(ans.get("strengths"))
            q_weaknesses = _parse_list(ans.get("weaknesses"))

            feedback_rows = []
            if q_strengths:
                s_paras = [Paragraph(f"&bull; {s}", styles["BulletItem"]) for s in q_strengths]
                feedback_rows.append([
                    Paragraph("<b>Strengths:</b>", styles["ReportBodyBold"]),
                    s_paras
                ])
            if q_weaknesses:
                w_paras = [Paragraph(f"&bull; {w}", styles["BulletItem"]) for w in q_weaknesses]
                feedback_rows.append([
                    Paragraph("<b>Areas for Improvement:</b>", styles["ReportBodyBold"]),
                    w_paras
                ])

            if feedback_rows:
                q_fb_table = Table(feedback_rows, colWidths=[110, content_width - 16 - 110])
                q_fb_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                    ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                q_elements.append(q_fb_table)

            # Outer wrapper card for question
            outer_q_card = Table([[q_elements]], colWidths=[content_width])
            outer_q_card.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.75, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ]))

            # Keep question evaluation together when possible
            story.append(KeepTogether(outer_q_card))
            story.append(Spacer(1, 8))

    # ==================================================
    # 12. OVERALL AI FEEDBACK
    # ==================================================
    fb_dict = feedback or {}
    ov_strengths = _parse_list(fb_dict.get("strengths") or (evaluation.get("strengths") if evaluation else None))
    ov_improvements = _parse_list(
        fb_dict.get("areas_to_improve") or fb_dict.get("weaknesses") or (evaluation.get("weaknesses") if evaluation else None)
    )
    tech_suggs = _parse_list(fb_dict.get("technical_suggestions"))
    comm_suggs = _parse_list(fb_dict.get("communication_suggestions"))
    conf_suggs = _parse_list(fb_dict.get("confidence_suggestions"))
    prob_suggs = _parse_list(fb_dict.get("problem_solving_suggestions"))
    practice_areas = _parse_list(fb_dict.get("practice_areas"))

    has_ai_feedback = any([
        ov_strengths, ov_improvements, tech_suggs,
        comm_suggs, conf_suggs, prob_suggs, practice_areas
    ])

    if has_ai_feedback:
        fb_elements = [
            Paragraph("AI Feedback & Recommendations", styles["SectionHeading"]),
            Spacer(1, 4),
        ]

        fb_table_rows = []
        if ov_strengths:
            s_paras = [Paragraph(f"&bull; {s}", styles["BulletItem"]) for s in ov_strengths]
            fb_table_rows.append([Paragraph("<b>Key Strengths</b>", styles["ReportBodyBold"]), s_paras])

        if ov_improvements:
            i_paras = [Paragraph(f"&bull; {i}", styles["BulletItem"]) for i in ov_improvements]
            fb_table_rows.append([Paragraph("<b>Areas to Improve</b>", styles["ReportBodyBold"]), i_paras])

        if tech_suggs:
            t_paras = [Paragraph(f"&bull; {t}", styles["BulletItem"]) for t in tech_suggs]
            fb_table_rows.append([Paragraph("<b>Technical Skills</b>", styles["ReportBodyBold"]), t_paras])

        if comm_suggs:
            c_paras = [Paragraph(f"&bull; {c}", styles["BulletItem"]) for c in comm_suggs]
            fb_table_rows.append([Paragraph("<b>Communication</b>", styles["ReportBodyBold"]), c_paras])

        if conf_suggs:
            cf_paras = [Paragraph(f"&bull; {cf}", styles["BulletItem"]) for cf in conf_suggs]
            fb_table_rows.append([Paragraph("<b>Confidence</b>", styles["ReportBodyBold"]), cf_paras])

        if prob_suggs:
            p_paras = [Paragraph(f"&bull; {p}", styles["BulletItem"]) for p in prob_suggs]
            fb_table_rows.append([Paragraph("<b>Problem Solving</b>", styles["ReportBodyBold"]), p_paras])

        if practice_areas:
            pa_paras = [Paragraph(f"&bull; {pa}", styles["BulletItem"]) for pa in practice_areas]
            fb_table_rows.append([Paragraph("<b>Practice Areas</b>", styles["ReportBodyBold"]), pa_paras])

        fb_table = Table(fb_table_rows, colWidths=[120, content_width - 120])
        fb_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
            ("BOX", (0, 0), (-1, -1), 0.75, c_border),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        fb_elements.append(fb_table)
        story.append(KeepTogether(fb_elements))
        story.append(Spacer(1, 10))

    # ==================================================
    # 13. TRANSCRIPT
    # ==================================================
    transcript_text = (interview.get("transcript") or "").strip()
    if transcript_text:
        trans_elements = [
            Paragraph("Interview Transcript", styles["SectionHeading"]),
            Spacer(1, 3),
        ]
        trans_table = Table([[Paragraph(transcript_text, styles["AnswerBody"])]], colWidths=[content_width])
        trans_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
            ("BOX", (0, 0), (-1, -1), 0.5, c_border),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        trans_elements.append(trans_table)
        trans_elements.append(Spacer(1, 3))
        trans_elements.append(Paragraph("<i>Speech transcription generated by Faster-Whisper.</i>", styles["ReportBodyMuted"]))
        story.append(KeepTogether(trans_elements))
        story.append(Spacer(1, 10))

    # ==================================================
    # 14. RECORDING INFORMATION
    # ==================================================
    rec_elements = [
        Paragraph("Recording Information", styles["SectionHeading"]),
        Spacer(1, 3),
    ]
    rec_msg = (
        "Interview recording captured and stored securely in system storage."
        if recording_available
        else "No session recording available for this interview."
    )
    rec_table = Table([[
        Paragraph(
            f"<b>Interview Recording:</b> {'Available' if recording_available else 'Unavailable'}<br/>{rec_msg}",
            styles["ReportBody"]
        )
    ]], colWidths=[content_width])
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
        ("BOX", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    rec_elements.append(rec_table)
    story.append(KeepTogether(rec_elements))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
