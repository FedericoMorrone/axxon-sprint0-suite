"""
ado_client.py — Cliente compartido de Azure DevOps para las skills de Axxon Consulting.

Repo canónico: axxon-ado-connector. Este archivo se vendoriza (se copia tal cual) dentro de
cada skill que lo necesita (ado-daily-prep, ado-us-planner, backlog-seeder, y las que sigan) —
no se referencia por ruta entre plugins. Si se corrige un bug o se agrega una función acá,
hay que re-copiarlo a cada consumidor; ver README.md de este repo para la lista de consumidores
vigentes.

Cubre: autenticación PAT, WIQL, CRUD de work items, paginación, retry con backoff exponencial,
y excepciones tipadas para que cada skill pueda dar mensajes de error específicos en vez de
un traceback crudo.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from typing import Any, Iterator

import requests

API_VERSION = "7.1"
DEFAULT_TIMEOUT = 30  # segundos
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0


# ---------------------------------------------------------------------------
# Excepciones tipadas
# ---------------------------------------------------------------------------

class AdoError(Exception):
    """Base de todas las excepciones de este módulo."""
    def __init__(self, message: str, status_code: int | None = None, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class AdoAuthError(AdoError):
    """PAT inválido, expirado, o sin permisos suficientes (401/403)."""


class AdoNotFoundError(AdoError):
    """Work item, proyecto, o recurso inexistente (404)."""


class AdoRateLimitError(AdoError):
    """Rate limit de Azure DevOps alcanzado (429) — reintentable."""


class AdoValidationError(AdoError):
    """El payload enviado no pasa validación del lado de Azure DevOps (400)."""


# ---------------------------------------------------------------------------
# Modelos livianos (no ORM — solo para tipar retornos, evitar dicts sueltos)
# ---------------------------------------------------------------------------

@dataclass
class WorkItem:
    id: int
    rev: int
    fields: dict[str, Any]
    url: str
    relations: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def title(self) -> str:
        return self.fields.get("System.Title", "")

    @property
    def work_item_type(self) -> str:
        return self.fields.get("System.WorkItemType", "")

    @property
    def state(self) -> str:
        return self.fields.get("System.State", "")

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "WorkItem":
        """Construye un WorkItem desde la respuesta cruda de la API, preservando `relations`
        y cualquier otro campo top-level (ej. comentarios cuando se pidió `$expand=all`) en
        `.raw` para que no se pierda nada silenciosamente."""
        return cls(
            id=data["id"], rev=data["rev"], fields=data["fields"], url=data["url"],
            relations=data.get("relations", []), raw=data,
        )


@dataclass
class WiqlResult:
    work_item_ids: list[int]
    raw: dict[str, Any] = field(repr=False)


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

class AdoClient:
    """
    Cliente REST para Azure DevOps, autenticado con Personal Access Token (PAT).

    Uso:
        client = AdoClient(organization="axxon", project="ClienteX", pat="xxxx")
        wi = client.create_work_item("Epic", {"System.Title": "Mi épica"})
    """

    def __init__(self, organization: str, project: str, pat: str, timeout: int = DEFAULT_TIMEOUT):
        if not pat:
            raise AdoAuthError("PAT vacío — no se puede autenticar contra Azure DevOps.")
        self.organization = organization
        self.project = project
        self.timeout = timeout
        self._base_url = f"https://dev.azure.com/{organization}/{project}/_apis"
        token = base64.b64encode(f":{pat}".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json-patch+json",
            "Accept": "application/json",
        }
        self._headers_json = {**self._headers, "Content-Type": "application/json"}

    # -- infraestructura interna ------------------------------------------------

    def _request(self, method: str, url: str, *, json_body: Any = None,
                 use_patch_content_type: bool = False, params: dict | None = None) -> dict:
        headers = self._headers if use_patch_content_type else self._headers_json
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.request(
                    method, url, headers=headers, json=json_body, params=params,
                    timeout=self.timeout,
                )
            except requests.exceptions.RequestException as exc:
                last_error = exc
                if attempt == MAX_RETRIES:
                    raise AdoError(f"Fallo de red contra Azure DevOps tras {MAX_RETRIES} intentos: {exc}") from exc
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                continue

            if response.status_code == 429:
                if attempt == MAX_RETRIES:
                    raise AdoRateLimitError(
                        "Rate limit de Azure DevOps alcanzado — reintentar más tarde.",
                        status_code=429,
                    )
                retry_after = float(response.headers.get("Retry-After", BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))))
                time.sleep(retry_after)
                continue

            if response.status_code >= 500:
                if attempt == MAX_RETRIES:
                    raise AdoError(
                        f"Azure DevOps devolvió error {response.status_code} tras {MAX_RETRIES} intentos.",
                        status_code=response.status_code, details=response.text[:500],
                    )
                time.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                continue

            self._raise_for_status(response)
            return response.json() if response.content else {}

        # No debería llegar acá, pero por completitud:
        raise AdoError(f"Fallo desconocido contra Azure DevOps: {last_error}")

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        if response.ok:
            return
        status = response.status_code
        try:
            body = response.json()
            message = body.get("message", response.text[:500])
        except ValueError:
            message = response.text[:500]

        if status in (401, 403):
            raise AdoAuthError(
                f"Sin autorización contra Azure DevOps (HTTP {status}) — verificar el PAT y sus scopes.",
                status_code=status, details=message,
            )
        if status == 404:
            raise AdoNotFoundError(
                f"Recurso no encontrado en Azure DevOps (HTTP 404): {message}",
                status_code=404, details=message,
            )
        if status == 400:
            raise AdoValidationError(
                f"Azure DevOps rechazó el request (HTTP 400): {message}",
                status_code=400, details=message,
            )
        raise AdoError(f"Error de Azure DevOps (HTTP {status}): {message}", status_code=status, details=message)

    # -- work items ---------------------------------------------------------

    def get_work_item(self, work_item_id: int, expand: str = "None") -> WorkItem:
        url = f"{self._base_url}/wit/workitems/{work_item_id}"
        data = self._request("GET", url, params={"api-version": API_VERSION, "$expand": expand})
        return WorkItem.from_api(data)

    def create_work_item(self, work_item_type: str, fields: dict[str, Any],
                          area_path: str | None = None, iteration_path: str | None = None,
                          relations: list[dict] | None = None) -> WorkItem:
        """
        Crea un work item. `fields` usa nombres cortos ('Title', 'Description') o completos
        ('System.Title') indistintamente — se normalizan acá.
        """
        ops = []
        for key, value in fields.items():
            field_ref = key if "." in key else f"System.{key}"
            ops.append({"op": "add", "path": f"/fields/{field_ref}", "value": value})

        if area_path:
            ops.append({"op": "add", "path": "/fields/System.AreaPath", "value": area_path})
        if iteration_path:
            ops.append({"op": "add", "path": "/fields/System.IterationPath", "value": iteration_path})
        for rel in (relations or []):
            ops.append({"op": "add", "path": "/relations/-", "value": rel})

        url = f"{self._base_url}/wit/workitems/${work_item_type}"
        data = self._request("PATCH", url, json_body=ops, use_patch_content_type=True,
                              params={"api-version": API_VERSION})
        return WorkItem.from_api(data)

    def update_work_item(self, work_item_id: int, fields: dict[str, Any]) -> WorkItem:
        ops = []
        for key, value in fields.items():
            field_ref = key if "." in key else f"System.{key}"
            ops.append({"op": "add", "path": f"/fields/{field_ref}", "value": value})
        url = f"{self._base_url}/wit/workitems/{work_item_id}"
        data = self._request("PATCH", url, json_body=ops, use_patch_content_type=True,
                              params={"api-version": API_VERSION})
        return WorkItem.from_api(data)

    def link_work_items(self, parent_id: int, child_id: int,
                         link_type: str = "System.LinkTypes.Hierarchy-Forward") -> WorkItem:
        """Enlaza `child_id` como hijo de `parent_id` (por defecto: relación padre/hijo)."""
        child_url = f"{self._base_url.rsplit('/apis', 1)[0]}/_apis/wit/workItems/{child_id}"
        ops = [{
            "op": "add", "path": "/relations/-",
            "value": {"rel": link_type, "url": child_url},
        }]
        url = f"{self._base_url}/wit/workitems/{parent_id}"
        data = self._request("PATCH", url, json_body=ops, use_patch_content_type=True,
                              params={"api-version": API_VERSION})
        return WorkItem.from_api(data)

    # -- WIQL -----------------------------------------------------------------

    def run_wiql(self, query: str) -> WiqlResult:
        url = f"{self._base_url}/wit/wiql"
        data = self._request("POST", url, json_body={"query": query},
                              params={"api-version": API_VERSION})
        ids = [wi["id"] for wi in data.get("workItems", [])]
        return WiqlResult(work_item_ids=ids, raw=data)

    def get_work_items_batch(self, ids: list[int], fields: list[str] | None = None,
                              expand: str | None = None) -> list[WorkItem]:
        """
        Trae varios work items en batches de 200 (límite de la API de Azure DevOps).

        `expand` acepta los valores de la API (`"all"`, `"relations"`, `"fields"`, `"links"`,
        `"none"`) — usar `"all"` para traer comentarios/revisiones recientes junto con los
        campos. No combinar `fields` y `expand="all"` — la API de Azure DevOps ignora `fields`
        cuando `expand` está presente.
        """
        results: list[WorkItem] = []
        for chunk in self._chunk(ids, 200):
            url = f"{self._base_url}/wit/workitems"
            params = {"ids": ",".join(map(str, chunk)), "api-version": API_VERSION}
            if expand:
                params["$expand"] = expand
            elif fields:
                params["fields"] = ",".join(fields)
            data = self._request("GET", url, params=params)
            for item in data.get("value", []):
                results.append(WorkItem.from_api(item))
        return results

    @staticmethod
    def _chunk(items: list, size: int) -> Iterator[list]:
        for i in range(0, len(items), size):
            yield items[i:i + size]

    # -- Areas / Iterations -----------------------------------------------------

    def list_iterations(self, team: str | None = None) -> list[dict]:
        team_segment = f"/{team}" if team else ""
        url = f"https://dev.azure.com/{self.organization}/{self.project}{team_segment}/_apis/work/teamsettings/iterations"
        data = self._request("GET", url, params={"api-version": API_VERSION})
        return data.get("value", [])
