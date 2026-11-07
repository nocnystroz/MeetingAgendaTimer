"""Local, explicitly selected exports. Never include configuration or credentials."""

from html import escape

from .engine import format_time


def markdown(meeting, notes=True, decisions=True, tasks=True, transcripts=False):
    parts = ["# Podsumowanie spotkania\n"]
    for index, item in enumerate(meeting.items, 1):
        parts.append(f"## {index}. {item.title}\n\nCzas: {format_time(item.seconds)}\n")
        if notes and item.notes:
            parts.append(f"### Notatki\n\n{item.notes}\n")
        if decisions and item.decisions:
            parts.append(f"### Decyzje\n\n{item.decisions}\n")
        if tasks and item.tasks:
            parts.append("### Zadania\n")
            for task in item.tasks:
                parts.append(f"- [{'x' if task.done else ' '}] {task.text} "
                             f"— {task.owner or 'nie przypisano'}; termin: {task.due or 'brak'}")
            parts.append("")
    if transcripts:
        for transcript in meeting.transcripts:
            parts.append(f"## Transkrypcja\n\n{transcript.get('text', '')}\n")
    return "\n".join(parts)


def pdf_document(meeting, **options):
    # Treat content as plain text. Never load images/URLs embedded in user notes.
    from PySide6.QtGui import QTextDocument
    document = QTextDocument()
    document.setDefaultStyleSheet("body { font-family: sans-serif; font-size: 11pt; color: #192d39; } h1 { color: #168f83; } h2 { margin-top: 24px; } p { white-space: pre-wrap; }")
    parts = ["<h1>Podsumowanie spotkania</h1>"]
    for index, item in enumerate(meeting.items, 1):
        parts.append(f"<h2>{index}. {escape(item.title)}</h2><p>Czas: {format_time(item.seconds)}</p>")
        for key, title in (("notes", "Notatki"), ("decisions", "Decyzje")):
            if options.get(key, True) and (text := getattr(item, key)):
                parts.append(f"<h3>{title}</h3><p>{escape(text)}</p>")
        if options.get("tasks", True) and item.tasks:
            parts.append("<h3>Zadania</h3><ul>")
            for task in item.tasks:
                text = f"{'[x]' if task.done else '[ ]'} {task.text} — {task.owner or 'nie przypisano'}; termin: {task.due or 'brak'}"
                parts.append(f"<li>{escape(text)}</li>")
            parts.append("</ul>")
    if options.get("transcripts", False):
        for transcript in meeting.transcripts:
            parts.append("<h2>Transkrypcja</h2><p>" + escape(transcript.get("text", "")) + "</p>")
    document.setHtml("<html><body>" + "".join(parts) + "</body></html>")
    return document
