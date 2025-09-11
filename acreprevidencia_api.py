# acreprevidencia_api.py
from __future__ import annotations
import time
import re
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class AcrePrevAPIError(Exception):
    """Erro genérico ao acessar a API do Acreprevidência."""


class DadosAcreprevidencia:
    BASE_AUTH = "http://www.acreprevidencia.ac.gov.br/security/jwt/token"
    BASE_API  = "http://www.acreprevidencia.ac.gov.br/api-tce/pedido?cpf="

    def __init__(
        self,
        timeout: float = 15.0,
        max_retries: int = 3,
        backoff_factor: float = 0.3,
    ) -> None:
        self.username = "tce_api_concessao"
        self.password = "Tce@Prev"
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_exp: Optional[float] = None  # epoch millis (segundo doc)
        # sessão com retry
        self.session = requests.Session()
        retries = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST"),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # ------------------------
    # Helpers
    # ------------------------
    @staticmethod
    def _only_digits(value: str) -> str:
        return re.sub(r"\D", "", value or "")

    def _headers(self) -> Dict[str, str]:
        if not self._token or self._is_token_expired():
            self.gerar_token()
        return {"Authorization": f"Bearer {self._token}"}

    def _is_token_expired(self) -> bool:
        # API retorna "expiration" em epoch millis; colocamos margem de segurança de 30s
        if self._token_exp is None:
            return True
        now_ms = time.time() * 1000
        return now_ms >= (self._token_exp - 30_000)

    # ------------------------
    # Autenticação
    # ------------------------
    def gerar_token(self) -> str:
        try:
            resp = self.session.post(
                self.BASE_AUTH,
                json={"username": self.username, "password": self.password},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise AcrePrevAPIError(f"Falha de conexão ao gerar token: {e}") from e

        if resp.status_code != 200:
            # tenta extrair mensagem útil
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
            raise AcrePrevAPIError(
                f"Erro ao obter token (HTTP {resp.status_code}): {data}"
            )

        try:
            data = resp.json()
            self._token = data.get("token")
            self._token_exp = float(data.get("expiration")) if data.get("expiration") else None
        except Exception as e:
            raise AcrePrevAPIError(f"Resposta inválida ao gerar token: {e}") from e

        if not self._token:
            raise AcrePrevAPIError("Token não retornado pela API.")
        return self._token

    # ------------------------
    # Endpoints
    # ------------------------
    def consultar(self, cpf: str) -> List[Dict[str, Any]]:
        """
        GET /api-tce/pedido/{cpf}
        Retorna uma lista de objetos (ver documentação).
        """
        cpf_digits = self._only_digits(cpf)
        if len(cpf_digits) != 11:
            raise ValueError("CPF deve conter 11 dígitos.")

        url = f"{self.BASE_API}{cpf_digits}"
        try:
            resp = self.session.get(url, headers=self._headers(), timeout=self.timeout)
        except requests.RequestException as e:
            raise AcrePrevAPIError(f"Falha de conexão ao consultar pedido: {e}") from e

        if resp.status_code == 404:
            # Sem pedidos para esse CPF
            return []

        if resp.status_code != 200:
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}
            raise AcrePrevAPIError(
                f"Erro na consulta (HTTP {resp.status_code}): {data}"
            )

        try:
            return resp.json()  # conforme doc, retorna um array
        except Exception as e:
            raise AcrePrevAPIError(f"Resposta JSON inválida: {e}") from e

    # ------------------------
    # (Opcional) Normalização
    # ------------------------
    #@staticmethod
    def getRegistroPorCPF(self, cpf: str)-> Optional[Dict[str, Any]]:
        return self.getRegistro(self.consultar(cpf))

    def getRegistro(self, pedidos: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Ajuda a puxar rapidamente dados comuns do último resultado.
        Retorna um dicionário já “achatado” contendo campos frequentes.
        """
        if not pedidos:
            return None
                
        registro = pedidos[len(pedidos)-1]  # último item
        out: Dict[str, Any] = {}

        # FUNCIONAL (lista)
        funcional = (registro.get("FUNCIONAL") or [])
        if funcional:
            f = funcional[len(funcional)-1]
            out.update({
                "Matricula": f.get("SERVIDOR"),
                "Contrato": f.get("CONTRATO"),
                "CPF": f.get("CPF"),
                "Nome": f.get("NOME"),
                "Sexo": f.get("SEXO"), 
                "Idade": f.get("IDADE"), 
                "Nascimento": f.get("NASCIMENTO"), 
                "Cargo": f.get("CARGO"),
                "Classe": f.get("CLASSE"),
                "Orgao": f.get("ORGAO"),
            })

        # APOSENTADORIA (lista)
        aposentadoria = (registro.get("APOSENTADORIA") or [])
        if aposentadoria:
            a = aposentadoria[len(aposentadoria)-1]
            out.update({
                "Processo_Administrativo": a.get("PROCESSO_ADM"), #NÃO MAPEADO
                "Tempo_Contribuicao": a.get("TEMPO_LIQUIDO_TOTAL"), #NÃO MAPEADO
                "Tempo_Contribuicao_Texto": a.get("TEMPO_LIQUIDO_TEXTO"), #NÃO MAPEADO
                "Tempo_Contribuicao_Ano": a.get("ANOS_LIQUIDO"),
                "Tempo_Contribuicao_Dias": a.get("DIAS_LIQUIDO"),
                "Proventos": a.get("PROVENTO"),
                "Data_concessao": a.get("DATA_CONCESSAO"),
                "Data_ingresso_cargo": a.get("ING_CARGO"), 
                "Data_ingresso_servico_publico": a.get("ING_SERVPUBLICO"), 
                "Fundamentacao": a.get("FUNDAMENTACAO"),
                "Descricao": a.get("DESCRICAO"),
            })

        return out
