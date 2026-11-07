"""Local, explicitly selected exports. Never include configuration or credentials."""

from html import escape

from .engine import format_time
from .i18n import tr


def markdown(meeting, notes=True, decisions=True, tasks=True, transcripts=False):
    parts = ["# " + tr("Podsumowanie spotkania") + "\n"]
    for index, item in enumerate(meeting.items, 1):
        parts.append(f"## {index}. {item.title}\n\n{tr('Czas')}: {format_time(item.seconds)}\n")
        if notes and item.notes:
            parts.append(f"### {tr('Notatki')}\n\n{item.notes}\n")
        if decisions and item.decisions:
            parts.append(f"### {tr('Decyzje')}\n\n{item.decisions}\n")
        if tasks and item.tasks:
            parts.append("### " + tr("Zadania") + "\n")
            for task in item.tasks:
                parts.append(f"- [{'x' if task.done else ' '}] {task.text} "
                             f"— {task.owner or tr('nie przypisano')}; {tr('termin')}: {task.due or tr('brak')}")
            parts.append("")
    if transcripts:
        for transcript in meeting.transcripts:
            parts.append(f"## {tr('Transkrypcja')}\n\n{transcript.get('text', '')}\n")
    return "\n".join(parts)


def pdf_document(meeting, **options):
    # Treat content as plain text. Never load images/URLs embedded in user notes.
    from PySide6.QtGui import QTextDocument
    document = QTextDocument()
    document.setDefaultStyleSheet("body { font-family: sans-serif; font-size: 11pt; color: #192d39; } h1 { color: #168f83; } h2 { margin-top: 24px; } p { white-space: pre-wrap; }")
    parts = ["<h1>" + escape(tr("Podsumowanie spotkania")) + "</h1>"]
    for index, item in enumerate(meeting.items, 1):
        parts.append(f"<h2>{index}. {escape(item.title)}</h2><p>{escape(tr('Czas'))}: {format_time(item.seconds)}</p>")
        for key, title in (("notes", "Notatki"), ("decisions", "Decyzje")):
            if options.get(key, True) and (text := getattr(item, key)):
                parts.append(f"<h3>{escape(tr(title))}</h3><p>{escape(text)}</p>")
        if options.get("tasks", True) and item.tasks:
            parts.append("<h3>" + escape(tr("Zadania")) + "</h3><ul>")
            for task in item.tasks:
                text = f"{'[x]' if task.done else '[ ]'} {task.text} — {task.owner or tr('nie przypisano')}; {tr('termin')}: {task.due or tr('brak')}"
                parts.append(f"<li>{escape(text)}</li>")
            parts.append("</ul>")
    if options.get("transcripts", False):
        for transcript in meeting.transcripts:
            parts.append("<h2>" + escape(tr("Transkrypcja")) + "</h2><p>" + escape(transcript.get("text", "")) + "</p>")
    document.setHtml("<html><body>" + "".join(parts) + "</body></html>")
    return document
