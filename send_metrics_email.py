#!/usr/bin/env python3
import os, glob, json, smtplib, pathlib
from email.message import EmailMessage
from email.utils import formatdate

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
MAIL_FROM = os.environ["MAIL_FROM"]
MAIL_TO   = os.environ["MAIL_TO"]
SUBJECT   = os.environ.get("SUBJECT", "EC2 Metrics Report")
METRICS_DIR = os.environ.get("METRICS_DIR", "./artifacts")

# Build HTML summary table from all JSONs
rows = []
for path in sorted(glob.glob(os.path.join(METRICS_DIR, "*.json"))):
    host = pathlib.Path(path).stem
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as e:
        data = {"error": str(e)}

    # Gracefully pull common fields if present in your template
    cpu = data.get("cpu", data.get("cpu_percent", data.get("cpu_usage", "n/a")))
    mem = data.get("memory", data.get("mem_used_percent", "n/a"))
    disk = data.get("disk", data.get("disk_used_percent", "n/a"))
    load = data.get("load_average", data.get("load", "n/a"))

    rows.append(f"""
        <tr>
          <td style="padding:6px;border:1px solid #ddd;">{host}</td>
          <td style="padding:6px;border:1px solid #ddd;">{cpu}</td>
          <td style="padding:6px;border:1px solid #ddd;">{mem}</td>
          <td style="padding:6px;border:1px solid #ddd;">{disk}</td>
          <td style="padding:6px;border:1px solid #ddd;">{load}</td>
        </tr>
    """)

table = f"""
  <h3>EC2 Metrics Summary</h3>
  <table style="border-collapse:collapse;">
    <thead>
      <tr>
        <th style="padding:6px;border:1px solid #ddd;">Host</th>
        <th style="padding:6px;border:1px solid #ddd;">CPU</th>
        <th style="padding:6px;border:1px solid #ddd;">Memory</th>
        <th style="padding:6px;border:1px solid #ddd;">Disk</th>
        <th style="padding:6px;border:1px solid #ddd;">Load</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows) if rows else '<tr><td colspan="5" style="padding:6px;border:1px solid #ddd;">No metrics files found</td></tr>'}
    </tbody>
  </table>
"""

msg = EmailMessage()
msg["From"] = MAIL_FROM
msg["To"] = MAIL_TO
msg["Date"] = formatdate(localtime=True)
msg["Subject"] = SUBJECT
msg.set_content("EC2 Metrics attached.\n\n(HTML summary included for quick view.)")
msg.add_alternative(table, subtype="html")

# Attach each JSON
for path in sorted(glob.glob(os.path.join(METRICS_DIR, "*.json"))):
    with open(path, "rb") as f:
        data = f.read()
    fname = pathlib.Path(path).name
    msg.add_attachment(data, maintype="application", subtype="json", filename=fname)

# Send
with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.send_message(msg)

print(f"Sent metrics email to {MAIL_TO} with {len(glob.glob(os.path.join(METRICS_DIR, '*.json')))} attachment(s).")

