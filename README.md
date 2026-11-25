# Expando — Guided Export Workspace

FastAPI + SQLAlchemy + SQLite (local default) with a static HTML/CSS/JS frontend. The application provides guided export-readiness interviews, an action-based roadmap, curated country intelligence with official source links, a decision-based Incoterms planner, export cost estimates, document uploads with a preliminary text rule engine, subscriptions, QRIS payment review, and role-based admin/user workspaces.

## Local setup (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Stop with Ctrl+C.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@expando.local | ChangeMe123! |
| User Free | free@expando.local | DemoFree123! |
| User Premium | premium@expando.local | DemoPremium123! |

Demo accounts are seeded when the app starts and only created if the email does not already exist. If you previously changed a demo password, the seeder will not reset it. For a clean local demo database, stop the server, back up and delete `expando.db`, then start the server again.

## Feature notes and limitations

- **Readiness interview:** seven guided steps, explanatory guidance, a weighted-equal 0–100 self-assessment score, and prioritized recommendations. It is not certification or a legal determination.
- **Roadmap:** generated action stages with why/how/evidence guidance and statuses (not started, in progress, blocked, done). It is not a plain checkbox list.
- **Country intelligence:** curated reference summaries for Singapore, Malaysia, Japan, Australia, Netherlands, and the United States. Free users can access Singapore and Malaysia; Premium users can access all listed countries. These summaries are not live feeds. Verify product-specific requirements, HS code, tariff, restrictions, and effective dates at the linked official authorities.
- **Shipping / Incoterms:** recommendation logic uses mode, container status, seller control, and buyer import capability. It is a decision aid, not legal advice. Confirm exact named place/port and contract wording with buyer and forwarder. Incoterms® is an ICC trademark; full authoritative rules require the ICC publication.
- **Document rule engine:** checks literal text indicators in supported text/PDF/DOCX formats. A missing keyword may be expressed differently; a found keyword does not prove legal validity. It does not verify authenticity, signatures, official templates, or regulator acceptance. Image-only PDFs and scans need OCR/manual review.
- **Payment:** QRIS is not bundled. Admin must upload the merchant's QRIS image and manually reconcile actual merchant settlement before approving payment.

## Database and uploads

SQLite is the local default. PostgreSQL can be used by setting `DATABASE_URL` to a SQLAlchemy PostgreSQL URL and installing a compatible PostgreSQL driver. Uploaded documents and payment proofs are stored in `uploads/`; production needs persistent object/file storage and backups. Do not rely on ephemeral filesystem storage on hosting platforms.

## Before production

1. Set a long random `SECRET_KEY` and strong unique admin password.
2. Use PostgreSQL and run a proper migration workflow (Alembic recommended).
3. Put uploads in persistent object storage; enforce file scanning and access controls.
4. Restrict CORS, enable HTTPS, configure rate limiting, logging, and backups.
5. Have export/customs specialists validate the rule sets, country content, and Incoterms guidance.
6. Never approve a payment based only on a screenshot; reconcile the merchant transaction.
