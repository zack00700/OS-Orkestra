"""
OS Orkestra — Script de seed (données de test)
Place ce fichier dans : backend/seed.py
Lance avec : cd backend && source venv/bin/activate && python seed.py
"""
import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import async_session_factory, init_db
from app.core.security import hash_password
from app.models.models import (
    User, Contact, Segment, SegmentMembership, Template, Campaign,
    CampaignEvent, AutomationScenario, SyncLog, DataQualityReport,
    UserRole, ContactSource, ContactStatus, CampaignStatus,
    CampaignType, ChannelType, LeadStage, EventType,
)


# ══════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════

COUNTRIES = ["France", "Maroc", "Sénégal", "Côte d'Ivoire", "Cameroun", "Tunisie", "Belgique", "Suisse", "Canada", "Congo"]
CITIES = {
    "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux"],
    "Maroc": ["Casablanca", "Rabat", "Marrakech", "Tanger", "Fès"],
    "Sénégal": ["Dakar", "Saint-Louis", "Thiès"],
    "Côte d'Ivoire": ["Abidjan", "Yamoussoukro", "Bouaké"],
    "Cameroun": ["Douala", "Yaoundé", "Bamenda"],
    "Tunisie": ["Tunis", "Sfax", "Sousse"],
    "Belgique": ["Bruxelles", "Anvers", "Gand"],
    "Suisse": ["Genève", "Zürich", "Lausanne"],
    "Canada": ["Montréal", "Québec", "Ottawa", "Toronto"],
    "Congo": ["Kinshasa", "Brazzaville", "Lubumbashi"],
}
COMPANIES = [
    "Groupe Meridian", "AfriTech Solutions", "Sahel Digital", "MedInsure Corp",
    "Atlas Logistics", "PanAfrica Energy", "NovaSoft", "EuroConnect",
    "TechBridge Africa", "Global Trade Partners", "OpenSID", "DataPulse",
    "SmartCity Labs", "AgriFuture", "FinanceHub", "CloudNine Systems",
    "Maritime Express", "SolarWave", "EduTech Pro", "HealthFirst Africa",
]
BUSINESS_UNITS = ["Commercial", "Marketing", "IT", "Finance", "RH", "Direction", "Opérations", "Logistique"]
SEGMENTS_DATA = ["Grands Comptes", "PME", "Panafricaines", "Internationales", "Startups", "Institutions"]
JOB_TITLES = [
    "Directeur Commercial", "Responsable Marketing", "Chef de Projet", "DSI",
    "Directeur Général", "Responsable RH", "Business Developer", "Consultant",
    "Analyste Data", "Ingénieur Cloud", "Responsable Digital", "Office Manager",
]
FIRST_NAMES = [
    "Amadou", "Fatima", "Moussa", "Aïcha", "Ibrahim", "Mariam", "Oumar", "Khadija",
    "Pierre", "Marie", "Jean", "Sophie", "Thomas", "Claire", "Nicolas", "Laura",
    "Youssef", "Nadia", "Rachid", "Samira", "David", "Sarah", "Mohammed", "Leila",
]
LAST_NAMES = [
    "Diallo", "Traoré", "Konaté", "Ba", "Ndiaye", "Sow", "Touré", "Camara",
    "Dupont", "Martin", "Bernard", "Dubois", "Laurent", "Moreau", "Garcia",
    "Benali", "El Fassi", "Ouédraogo", "Mbeki", "Nkosi", "Nguema", "Kabila",
]
DOMAINS = ["gmail.com", "outlook.com", "yahoo.fr", "company.com", "enterprise.africa", "proton.me"]


def random_date(start_days_ago, end_days_ago=0):
    """Date aléatoire entre start_days_ago et end_days_ago."""
    delta = random.randint(end_days_ago, start_days_ago)
    return datetime.now(timezone.utc) - timedelta(days=delta)


def random_email(first, last):
    domain = random.choice(DOMAINS)
    num = random.randint(100, 9999)
    return f"{first.lower()}.{last.lower()}.{num}@{domain}"


# ══════════════════════════════════════════════════════════
# SEED
# ══════════════════════════════════════════════════════════

async def seed():
    print("\n🌱 OS Orkestra — Seed des données de test\n")

    async with async_session_factory() as db:
        try:
            # ── 1. USERS ────────────────────────────────
            print("  [1/9] Création des utilisateurs...")
            users = []
            users_data = [
                ("admin@opensid.com", "Admin OpenSID", UserRole.ADMIN),
                ("zack@opensid.com", "Zack", UserRole.ADMIN),
                ("marketing@opensid.com", "Équipe Marketing", UserRole.MANAGER),
                ("commercial@opensid.com", "Équipe Commerciale", UserRole.EDITOR),
                ("viewer@opensid.com", "Viewer Test", UserRole.VIEWER),
            ]
            for email, name, role in users_data:
                user = User(
                    id=uuid.uuid4(),
                    email=email,
hashed_password="Test1234",
                    full_name=name,
                    role=role,
                    is_active=True,
                )
                db.add(user)
                users.append(user)
            await db.flush()
            print(f"    ✓ {len(users)} utilisateurs créés")

            # ── 2. SEGMENTS ─────────────────────────────
            print("  [2/9] Création des segments...")
            segments = []
            for seg_name in SEGMENTS_DATA:
                seg = Segment(
                    id=uuid.uuid4(),
                    name=seg_name,
                    description=f"Segment {seg_name} — contacts ciblés",
                    filter_criteria={"segment": seg_name},
                    is_dynamic=True,
                    contact_count=0,
                )
                db.add(seg)
                segments.append(seg)
            await db.flush()
            print(f"    ✓ {len(segments)} segments créés")

            # ── 3. CONTACTS (200 externes + 50 internes) ─
            print("  [3/9] Création des contacts...")
            contacts = []

            # Contacts externes
            for i in range(200):
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                country = random.choice(COUNTRIES)
                city = random.choice(CITIES[country])
                stage = random.choices(
                    [LeadStage.AWARENESS, LeadStage.INTEREST, LeadStage.CONSIDERATION, LeadStage.PURCHASE, LeadStage.RETENTION],
                    weights=[35, 25, 20, 12, 8],
                )[0]
                score_ranges = {
                    LeadStage.AWARENESS: (0, 19),
                    LeadStage.INTEREST: (20, 49),
                    LeadStage.CONSIDERATION: (50, 79),
                    LeadStage.PURCHASE: (80, 95),
                    LeadStage.RETENTION: (60, 100),
                }
                sr = score_ranges[stage]

                contact = Contact(
                    id=uuid.uuid4(),
                    email=random_email(first, last),
                    first_name=first,
                    last_name=last,
                    company=random.choice(COMPANIES),
                    job_title=random.choice(JOB_TITLES),
                    phone=f"+{random.randint(1,9)}{random.randint(100000000,999999999)}",
                    country=country,
                    city=city,
                    business_unit=random.choice(BUSINESS_UNITS),
                    segment=random.choice(SEGMENTS_DATA),
                    source=random.choice([ContactSource.CRM_DYNAMICS, ContactSource.WEBFORM, ContactSource.IMPORT_CSV, ContactSource.MANUAL]),
                    status=random.choices(
                        [ContactStatus.ACTIVE, ContactStatus.INACTIVE, ContactStatus.UNSUBSCRIBED],
                        weights=[80, 12, 8],
                    )[0],
                    lead_stage=stage,
                    lead_score=random.randint(sr[0], sr[1]),
                    is_internal=False,
                    gdpr_consent=random.choice([True, True, True, False]),
                    gdpr_consent_date=random_date(365) if random.random() > 0.3 else None,
                    tags=random.sample(["newsletter", "webinar", "demo", "whitepaper", "event", "vip", "prospect"], k=random.randint(1, 3)),
                    created_at=random_date(365, 30),
                    updated_at=random_date(30),
                )
                db.add(contact)
                contacts.append(contact)

            # Contacts internes (collaborateurs)
            for i in range(50):
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                contact = Contact(
                    id=uuid.uuid4(),
                    email=f"{first.lower()}.{last.lower()}.{i}@opensid.com",
                    first_name=first,
                    last_name=last,
                    company="OpenSID",
                    job_title=random.choice(JOB_TITLES),
                    country="France",
                    city=random.choice(["Paris", "Lyon", "Marseille"]),
                    business_unit=random.choice(BUSINESS_UNITS),
                    source=ContactSource.AZURE_AD,
                    status=ContactStatus.ACTIVE,
                    lead_stage=LeadStage.RETENTION,
                    lead_score=0,
                    is_internal=True,
                    gdpr_consent=True,
                    tags=["collaborateur", "interne"],
                    created_at=random_date(365, 60),
                    updated_at=random_date(30),
                )
                db.add(contact)
                contacts.append(contact)

            await db.flush()
            print(f"    ✓ {len(contacts)} contacts créés (200 externes + 50 internes)")

            # Mettre à jour le count des segments
            for seg in segments:
                count = sum(1 for c in contacts if c.segment == seg.name)
                seg.contact_count = count

            # ── 4. SEGMENT MEMBERSHIPS ──────────────────
            print("  [4/9] Association contacts → segments...")
            memberships = 0
            for contact in contacts:
                if contact.segment:
                    matching = [s for s in segments if s.name == contact.segment]
                    if matching:
                        sm = SegmentMembership(
                            id=uuid.uuid4(),
                            contact_id=contact.id,
                            segment_id=matching[0].id,
                        )
                        db.add(sm)
                        memberships += 1
            await db.flush()
            print(f"    ✓ {memberships} associations créées")

            # ── 5. TEMPLATES ────────────────────────────
            print("  [5/9] Création des templates email...")
            templates = []
            templates_data = [
                ("Newsletter Mensuelle", "📰 Les actualités du mois — {{company}}", "newsletter"),
                ("Bienvenue", "Bienvenue chez {{company}}, {{first_name}} !", "welcome"),
                ("Invitation Webinar", "🎯 Webinar exclusif : {{topic}}", "event"),
                ("Offre Spéciale", "🎁 Offre spéciale pour vous, {{first_name}}", "promo"),
                ("Satisfaction Client", "Votre avis compte — {{company}}", "survey"),
                ("Relance Prospect", "{{first_name}}, avez-vous vu notre dernière offre ?", "nurturing"),
                ("Info Collaborateurs", "📋 Infos internes — Semaine {{week}}", "internal"),
                ("Événement Annuel", "🎉 Save the Date — Événement annuel {{year}}", "event"),
            ]
            for name, subject, category in templates_data:
                tpl = Template(
                    id=uuid.uuid4(),
                    name=name,
                    subject=subject,
                    html_content=f"<html><body><h1>{name}</h1><p>Contenu du template {name}</p></body></html>",
                    text_content=f"{name}\n\nContenu texte du template.",
                    category=category,
                    variables=["first_name", "company"],
                    is_active=True,
                )
                db.add(tpl)
                templates.append(tpl)
            await db.flush()
            print(f"    ✓ {len(templates)} templates créés")

            # ── 6. CAMPAIGNS ───────────────────────────
            print("  [6/9] Création des campagnes...")
            campaigns = []
            campaigns_data = [
                ("Newsletter Mars 2026", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.COMPLETED, 120),
                ("Newsletter Février 2026", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.COMPLETED, 90),
                ("Webinar IA & Data", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.COMPLETED, 60),
                ("Offre Printemps 2026", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.RUNNING, 15),
                ("Welcome Series — Nouveaux", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.RUNNING, 30),
                ("Info Collaborateurs Q1", CampaignType.INTERNAL, ChannelType.EMAIL, CampaignStatus.COMPLETED, 45),
                ("Promo WhatsApp Afrique", CampaignType.EXTERNAL, ChannelType.WHATSAPP, CampaignStatus.COMPLETED, 30),
                ("Satisfaction Client 2025", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.COMPLETED, 150),
                ("Relance Prospects Inactifs", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.SCHEDULED, 0),
                ("Newsletter Avril 2026", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.DRAFT, 0),
                ("Événement Annuel 2026", CampaignType.EXTERNAL, ChannelType.EMAIL, CampaignStatus.SCHEDULED, 0),
                ("Info RH — Nouveaux Avantages", CampaignType.INTERNAL, ChannelType.EMAIL, CampaignStatus.COMPLETED, 20),
            ]

            for name, ctype, channel, status, days_ago in campaigns_data:
                sent = random.randint(800, 12000) if status in (CampaignStatus.COMPLETED, CampaignStatus.RUNNING) else 0
                delivered = int(sent * random.uniform(0.94, 0.99)) if sent > 0 else 0
                opened = int(delivered * random.uniform(0.35, 0.65)) if delivered > 0 else 0
                clicked = int(opened * random.uniform(0.25, 0.55)) if opened > 0 else 0
                bounced = sent - delivered if sent > 0 else 0
                unsub = int(sent * random.uniform(0.001, 0.008)) if sent > 0 else 0

                camp = Campaign(
                    id=uuid.uuid4(),
                    name=name,
                    description=f"Campagne {name}",
                    campaign_type=ctype,
                    channel=channel,
                    status=status,
                    template_id=random.choice(templates).id,
                    segment_id=random.choice(segments).id,
                    subject=f"[OpenSID] {name}",
                    from_name="OpenSID Marketing",
                    from_email="marketing@opensid.com",
                    scheduled_at=random_date(days_ago + 5, days_ago) if days_ago > 0 else None,
                    sent_at=random_date(days_ago, max(0, days_ago - 2)) if status in (CampaignStatus.COMPLETED, CampaignStatus.RUNNING) else None,
                    completed_at=random_date(max(0, days_ago - 3)) if status == CampaignStatus.COMPLETED else None,
                    created_by=users[0].id,
                    tags=random.sample(["newsletter", "promo", "event", "nurturing", "interne", "afrique", "europe"], k=random.randint(1, 3)),
                    total_sent=sent,
                    total_delivered=delivered,
                    total_opened=opened,
                    total_clicked=clicked,
                    total_bounced=bounced,
                    total_unsubscribed=unsub,
                    created_at=random_date(days_ago + 10, days_ago + 5),
                    updated_at=random_date(days_ago, 0),
                )
                db.add(camp)
                campaigns.append(camp)
            await db.flush()
            print(f"    ✓ {len(campaigns)} campagnes créées")

            # ── 7. CAMPAIGN EVENTS (échantillon) ────────
            print("  [7/9] Génération des événements de tracking...")
            events_count = 0
            active_contacts = [c for c in contacts if not c.is_internal and c.status == ContactStatus.ACTIVE]

            for camp in campaigns:
                if camp.total_sent == 0:
                    continue
                # Prendre un échantillon de contacts pour chaque campagne
                sample_size = min(len(active_contacts), random.randint(30, 80))
                sample_contacts = random.sample(active_contacts, sample_size)

                for contact in sample_contacts:
                    # SENT
                    event_time = camp.sent_at or random_date(60, 10)
                    db.add(CampaignEvent(
                        id=uuid.uuid4(),
                        campaign_id=camp.id,
                        contact_id=contact.id,
                        event_type=EventType.SENT,
                        timestamp=event_time,
                    ))
                    events_count += 1

                    # DELIVERED (95%)
                    if random.random() < 0.95:
                        db.add(CampaignEvent(
                            id=uuid.uuid4(),
                            campaign_id=camp.id,
                            contact_id=contact.id,
                            event_type=EventType.DELIVERED,
                            timestamp=event_time + timedelta(seconds=random.randint(1, 30)),
                        ))
                        events_count += 1

                        # OPENED (40-60%)
                        if random.random() < random.uniform(0.4, 0.6):
                            open_time = event_time + timedelta(hours=random.randint(1, 48))
                            db.add(CampaignEvent(
                                id=uuid.uuid4(),
                                campaign_id=camp.id,
                                contact_id=contact.id,
                                event_type=EventType.OPENED,
                                timestamp=open_time,
                            ))
                            events_count += 1

                            # CLICKED (30-50% des ouvreurs)
                            if random.random() < random.uniform(0.3, 0.5):
                                db.add(CampaignEvent(
                                    id=uuid.uuid4(),
                                    campaign_id=camp.id,
                                    contact_id=contact.id,
                                    event_type=EventType.CLICKED,
                                    timestamp=open_time + timedelta(minutes=random.randint(1, 30)),
                                    url_clicked=random.choice([
                                        "https://opensid.com/offre",
                                        "https://opensid.com/webinar",
                                        "https://opensid.com/demo",
                                        "https://opensid.com/contact",
                                    ]),
                                ))
                                events_count += 1

            await db.flush()
            print(f"    ✓ {events_count} événements de tracking créés")

            # ── 8. AUTOMATION SCENARIOS ─────────────────
            print("  [8/9] Création des scénarios d'automatisation...")
            automations = [
                AutomationScenario(
                    id=uuid.uuid4(),
                    name="Welcome Series",
                    description="Série de bienvenue pour les nouveaux inscrits — 3 emails sur 7 jours",
                    trigger_type="form_submit",
                    trigger_config={"form_id": "signup", "delay_hours": 1},
                    steps=[
                        {"step": 1, "action": "send_email", "template": "Bienvenue", "delay": "0h"},
                        {"step": 2, "action": "wait", "duration": "3d"},
                        {"step": 3, "action": "send_email", "template": "Découverte services", "delay": "0h"},
                        {"step": 4, "action": "wait", "duration": "4d"},
                        {"step": 5, "action": "send_email", "template": "Offre premier achat", "delay": "0h"},
                    ],
                    is_active=True,
                    total_enrolled=342,
                    total_completed=287,
                ),
                AutomationScenario(
                    id=uuid.uuid4(),
                    name="Lead Nurturing B2B",
                    description="Nurturing des prospects B2B — scoring progressif sur 30 jours",
                    trigger_type="lead_score",
                    trigger_config={"min_score": 20, "segment": "Grands Comptes"},
                    steps=[
                        {"step": 1, "action": "send_email", "template": "Étude de cas", "delay": "0h"},
                        {"step": 2, "action": "wait", "duration": "7d"},
                        {"step": 3, "action": "check_score", "condition": "score >= 50"},
                        {"step": 4, "action": "send_email", "template": "Invitation démo", "delay": "0h"},
                        {"step": 5, "action": "notify_sales", "channel": "email"},
                    ],
                    is_active=True,
                    total_enrolled=156,
                    total_completed=89,
                ),
                AutomationScenario(
                    id=uuid.uuid4(),
                    name="Réactivation Inactifs",
                    description="Relance des contacts sans interaction depuis 90 jours",
                    trigger_type="inactivity",
                    trigger_config={"days_inactive": 90},
                    steps=[
                        {"step": 1, "action": "send_email", "template": "Vous nous manquez", "delay": "0h"},
                        {"step": 2, "action": "wait", "duration": "14d"},
                        {"step": 3, "action": "check_engagement", "condition": "opened_or_clicked"},
                        {"step": 4, "action": "send_email", "template": "Dernière chance", "delay": "0h"},
                    ],
                    is_active=False,
                    total_enrolled=0,
                    total_completed=0,
                ),
            ]
            for auto in automations:
                db.add(auto)
            await db.flush()
            print(f"    ✓ {len(automations)} scénarios créés")

            # ── 9. SYNC LOGS & DATA QUALITY ─────────────
            print("  [9/9] Création des logs de sync et rapports qualité...")

            # Sync logs
            for i in range(10):
                sync_date = random_date(30, 0)
                duration = random.uniform(2.5, 45.0)
                total = random.randint(500, 5000)
                errors = random.randint(0, 15)
                db.add(SyncLog(
                    id=uuid.uuid4(),
                    source=random.choice(["dynamics", "azure_ad"]),
                    direction="inbound",
                    total_records=total,
                    success_count=total - errors,
                    error_count=errors,
                    duplicate_count=random.randint(0, 50),
                    started_at=sync_date,
                    completed_at=sync_date + timedelta(seconds=duration),
                    duration_seconds=round(duration, 2),
                ))

            # Data quality reports
            for i in range(7):
                report_date = datetime.now(timezone.utc) - timedelta(days=i * 7)
                db.add(DataQualityReport(
                    id=uuid.uuid4(),
                    report_date=report_date,
                    total_contacts=250 - i * 5,
                    email_valid_pct=round(random.uniform(93.0, 97.0), 1),
                    field_completion_pct=round(random.uniform(78.0, 88.0), 1),
                    duplicate_count=random.randint(10, 50),
                    stale_count=random.randint(80, 200),
                    details={
                        "missing_phone": random.randint(20, 80),
                        "missing_company": random.randint(5, 30),
                        "invalid_emails": random.randint(3, 15),
                    },
                ))

            await db.flush()
            print(f"    ✓ 10 logs de sync + 7 rapports qualité créés")

            # ── COMMIT ──────────────────────────────────
            await db.commit()

            print("\n" + "=" * 50)
            print("  ✅ Seed terminé avec succès !")
            print("=" * 50)
            print(f"\n  Résumé :")
            print(f"    • {len(users)} utilisateurs")
            print(f"    • {len(contacts)} contacts (200 externes + 50 internes)")
            print(f"    • {len(segments)} segments")
            print(f"    • {len(templates)} templates email")
            print(f"    • {len(campaigns)} campagnes")
            print(f"    • {events_count} événements de tracking")
            print(f"    • {len(automations)} scénarios d'automatisation")
            print(f"    • 10 logs de sync + 7 rapports qualité")
            print(f"\n  Login test : admin@opensid.com / OpenSID2026!")
            print(f"  Login test : zack@opensid.com / OpenSID2026!")
            print()

        except Exception as e:
            await db.rollback()
            print(f"\n  ❌ Erreur : {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(seed())
