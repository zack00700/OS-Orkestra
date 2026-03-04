"""
OS HubLine — Connecteur Azure AD (Microsoft Entra ID)
Synchronisation de l'annuaire interne pour les campagnes internes.
"""
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger("hubline.integrations.azure_ad")
settings = get_settings()


class AzureADConnector:
    """Connecteur Microsoft Graph API pour Azure AD."""

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self.tenant_id = settings.AZURE_TENANT_ID
        self.client_id = settings.AZURE_CLIENT_ID
        self.client_secret = settings.AZURE_CLIENT_SECRET
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_token(self) -> str:
        """Obtenir un token via MSAL client credentials."""
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
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            return self._token

    async def _graph_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Requête authentifiée vers Microsoft Graph."""
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "ConsistencyLevel": "eventual",
        }
        url = f"{self.GRAPH_BASE}/{endpoint}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

    # ── Users ───────────────────────────────────────────

    async def fetch_users(
        self,
        department: Optional[str] = None,
        country: Optional[str] = None,
        top: int = 999,
    ) -> list[dict]:
        """Récupérer les utilisateurs depuis Azure AD."""
        select_fields = (
            "id,mail,displayName,givenName,surname,jobTitle,"
            "department,companyName,country,city,officeLocation,"
            "mobilePhone,businessPhones"
        )
        endpoint = f"users?$select={select_fields}&$top={top}"

        filters = ["accountEnabled eq true", "mail ne null"]
        if department:
            filters.append(f"department eq '{department}'")
        if country:
            filters.append(f"country eq '{country}'")

        endpoint += f"&$filter={' and '.join(filters)}"

        all_users = []
        while endpoint:
            data = await self._graph_request("GET", endpoint)
            all_users.extend(data.get("value", []))
            endpoint = data.get("@odata.nextLink", "").replace(f"{self.GRAPH_BASE}/", "")

        return all_users

    async def fetch_user_by_id(self, user_id: str) -> dict:
        """Récupérer un utilisateur spécifique."""
        return await self._graph_request("GET", f"users/{user_id}")

    # ── Groups ──────────────────────────────────────────

    async def fetch_groups(self) -> list[dict]:
        """Récupérer les groupes/listes de distribution."""
        data = await self._graph_request(
            "GET",
            "groups?$select=id,displayName,description,groupTypes,mail&$top=999"
        )
        return data.get("value", [])

    async def fetch_group_members(self, group_id: str) -> list[dict]:
        """Récupérer les membres d'un groupe."""
        data = await self._graph_request(
            "GET",
            f"groups/{group_id}/members?$select=id,mail,displayName,department,country"
        )
        return data.get("value", [])

    # ── Departments ─────────────────────────────────────

    async def fetch_departments(self) -> list[str]:
        """Lister les départements uniques."""
        data = await self._graph_request(
            "GET",
            "users?$select=department&$filter=department ne null&$top=999"
        )
        departments = set()
        for user in data.get("value", []):
            dept = user.get("department")
            if dept:
                departments.add(dept)
        return sorted(departments)

    # ── Mapping ─────────────────────────────────────────

    @staticmethod
    def map_to_hubline(ad_user: dict) -> dict:
        """Convertir un utilisateur Azure AD vers le format HubLine."""
        phones = ad_user.get("businessPhones", [])
        return {
            "email": ad_user.get("mail", ""),
            "first_name": ad_user.get("givenName", ""),
            "last_name": ad_user.get("surname", ""),
            "company": ad_user.get("companyName", ""),
            "job_title": ad_user.get("jobTitle", ""),
            "phone": ad_user.get("mobilePhone") or (phones[0] if phones else ""),
            "country": ad_user.get("country", ""),
            "city": ad_user.get("city", ""),
            "business_unit": ad_user.get("department", ""),
            "azure_ad_id": ad_user.get("id", ""),
            "source": "azure_ad",
            "is_internal": True,
        }

    async def test_connection(self) -> dict:
        """Tester la connexion à Azure AD."""
        try:
            await self._get_token()
            data = await self._graph_request("GET", "users?$top=1&$select=id")
            return {"status": "connected", "test_record": bool(data.get("value"))}
        except Exception as e:
            logger.error(f"Azure AD connection test failed: {e}")
            return {"status": "error", "message": str(e)}
