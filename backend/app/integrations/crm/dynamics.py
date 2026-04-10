"""
OS HubLine — Connecteur CRM Microsoft Dynamics 365
Synchronisation bidirectionnelle des contacts, leads et opportunités.
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger("hubline.integrations.dynamics")
settings = get_settings()


class DynamicsConnector:
    """Connecteur API Microsoft Dynamics 365."""

    def __init__(self):
        self.base_url = settings.DYNAMICS_BASE_URL
        self.client_id = settings.DYNAMICS_CLIENT_ID
        self.client_secret = settings.DYNAMICS_CLIENT_SECRET
        self.tenant_id = settings.DYNAMICS_TENANT_ID
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Obtenir un access token via OAuth 2.0 client credentials."""
        if self._token and self._token_expires and datetime.now(timezone.utc) < self._token_expires:
            return self._token

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": f"{self.base_url}/.default",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._token_expires = datetime.now(timezone.utc)
            return self._token

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Requête authentifiée vers Dynamics."""
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0",
            "Accept": "application/json",
        }
        url = f"{self.base_url}/api/data/v9.2/{endpoint}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return {}
            return response.json()

    # ── Contacts ────────────────────────────────────────

    async def fetch_contacts(
        self,
        modified_since: Optional[datetime] = None,
        top: int = 1000,
    ) -> list[dict]:
        """Récupérer les contacts depuis Dynamics (sync incrémentale)."""
        select_fields = (
            "contactid,emailaddress1,firstname,lastname,company,"
            "jobtitle,telephone1,address1_country,address1_city,modifiedon"
        )
        endpoint = f"contacts?$select={select_fields}&$top={top}&$orderby=modifiedon desc"

        if modified_since:
            iso_date = modified_since.strftime("%Y-%m-%dT%H:%M:%SZ")
            endpoint += f"&$filter=modifiedon gt {iso_date}"

        data = await self._request("GET", endpoint)
        return data.get("value", [])

    async def push_contact(self, contact_data: dict) -> dict:
        """Créer ou mettre à jour un contact dans Dynamics."""
        crm_id = contact_data.get("external_crm_id")
        payload = {
            "emailaddress1": contact_data["email"],
            "firstname": contact_data.get("first_name", ""),
            "lastname": contact_data.get("last_name", ""),
            "company": contact_data.get("company", ""),
            "jobtitle": contact_data.get("job_title", ""),
            "telephone1": contact_data.get("phone", ""),
            "address1_country": contact_data.get("country", ""),
            "address1_city": contact_data.get("city", ""),
        }

        if crm_id:
            await self._request("PATCH", f"contacts({crm_id})", json=payload)
            return {"action": "updated", "crm_id": crm_id}
        else:
            result = await self._request("POST", "contacts", json=payload)
            return {"action": "created", "crm_id": result.get("contactid")}

    async def delete_contact(self, crm_id: str) -> None:
        """Supprimer un contact dans Dynamics."""
        await self._request("DELETE", f"contacts({crm_id})")

    # ── Leads ───────────────────────────────────────────

    async def fetch_leads(
        self,
        modified_since: Optional[datetime] = None,
        top: int = 500,
    ) -> list[dict]:
        """Récupérer les leads depuis Dynamics."""
        select_fields = (
            "leadid,emailaddress1,firstname,lastname,companyname,"
            "jobtitle,telephone1,leadqualitycode,leadsourcecode,modifiedon"
        )
        endpoint = f"leads?$select={select_fields}&$top={top}&$orderby=modifiedon desc"

        if modified_since:
            iso_date = modified_since.strftime("%Y-%m-%dT%H:%M:%SZ")
            endpoint += f"&$filter=modifiedon gt {iso_date}"

        data = await self._request("GET", endpoint)
        return data.get("value", [])

    async def push_lead_score(self, lead_id: str, score: int) -> None:
        """Mettre à jour le score d'un lead dans Dynamics."""
        await self._request(
            "PATCH",
            f"leads({lead_id})",
            json={"leadqualitycode": self._map_score_to_quality(score)},
        )

    # ── Opportunités ────────────────────────────────────

    async def fetch_opportunities(
        self,
        modified_since: Optional[datetime] = None,
        top: int = 200,
    ) -> list[dict]:
        """Récupérer les opportunités pour l'attribution marketing."""
        select_fields = (
            "opportunityid,name,estimatedvalue,actualclosedate,"
            "stepname,statuscode,modifiedon"
        )
        endpoint = f"opportunities?$select={select_fields}&$top={top}&$orderby=modifiedon desc"

        if modified_since:
            iso_date = modified_since.strftime("%Y-%m-%dT%H:%M:%SZ")
            endpoint += f"&$filter=modifiedon gt {iso_date}"

        data = await self._request("GET", endpoint)
        return data.get("value", [])

    # ── Helpers ─────────────────────────────────────────

    @staticmethod
    def _map_score_to_quality(score: int) -> int:
        """Mapper le score interne vers leadqualitycode Dynamics."""
        if score >= 80:
            return 1  # Hot
        elif score >= 50:
            return 2  # Warm
        else:
            return 3  # Cold

    @staticmethod
    def map_to_hubline(dynamics_contact: dict) -> dict:
        """Convertir un contact Dynamics vers le format HubLine."""
        return {
            "email": dynamics_contact.get("emailaddress1", ""),
            "first_name": dynamics_contact.get("firstname", ""),
            "last_name": dynamics_contact.get("lastname", ""),
            "company": dynamics_contact.get("company", ""),
            "job_title": dynamics_contact.get("jobtitle", ""),
            "phone": dynamics_contact.get("telephone1", ""),
            "country": dynamics_contact.get("address1_country", ""),
            "city": dynamics_contact.get("address1_city", ""),
            "external_crm_id": dynamics_contact.get("contactid", ""),
            "source": "crm_dynamics",
        }

    async def test_connection(self) -> dict:
        """Tester la connexion à Dynamics."""
        try:
            await self._get_token()
            data = await self._request("GET", "contacts?$top=1&$select=contactid")
            return {"status": "connected", "test_record": bool(data.get("value"))}
        except Exception as e:
            logger.error(f"Dynamics connection test failed: {e}")
            return {"status": "error", "message": str(e)}
