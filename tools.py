import locale, re
from datetime import datetime
from num2words import num2words
from decimal import Decimal

class Tools:
    def DataAtual():
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        data_atual = datetime.now()
        return data_atual.strftime('%d de %B de %Y')

    def ValorPorExtenso(valor):
        inteiro = int(valor)
        centavos = int((valor - inteiro) * 100)
        texto_int = num2words(inteiro, lang='pt_BR')
        if centavos:
            texto_cen = num2words(centavos, lang='pt_BR')
            return f"{texto_int} reais e {texto_cen} centavos"
        return f"{texto_int} reais"
    
    def FormatarData(dt):
        return dt.strftime('%d/%m/%Y') if dt else ''

    def FormatarCPF(cpf_str):
        if not cpf_str or not isinstance(cpf_str, str):
            return ''
        
        # Remove qualquer caractere que não seja dígito
        cpf_digits = re.sub(r'\D', '', cpf_str)
        
        # Se não tiver 11 dígitos, retorna o que foi limpo (ou vazio)
        if len(cpf_digits) != 11:
            return cpf_digits
            
        return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"

    def PreencherDados(proc):
        dados = {
            "servidor": proc.servidor or '', "cpf": Tools.FormatarCPF(proc.cpf),
            "cargo": proc.cargo or '',
            "matricula": proc.matricula or '',
            "orgao": proc.orgao or '',
            "orgao_previdencia": proc.orgao_previdencia.nome if proc.orgao_previdencia else '',
            "classe": proc.classe.nome if proc.classe else '',
            "fundamento_legal": proc.fundamento_legal or '',
            "processo": proc.processo[:3] + '.' + proc.processo[3:],
            "proventos": f"R$ {proc.proventos:,.2f}"
                    .replace(",", "X").replace(".", ",").replace("X", ".")
                    if proc.proventos else "",
            "proventos_extenso": Tools.ValorPorExtenso(proc.proventos or Decimal('0.00')),
            "ato_concessorio": re.sub(r'(^\w{1}|\.\s*\w{1})', lambda x: x.group().upper(),  (proc.ato_concessorio or '').lower()),
            "data_ato_concessorio": Tools.FormatarData(proc.data_ato_concessorio),
            "publicacao": proc.publicacao or "",
            "data_publicacao": Tools.FormatarData(proc.data_publicacao),
            "anos_tempo_de_contribuicao": proc.anos_tempo_de_contribuicao or "",
            "dias_tempo_de_contribuicao": proc.dias_tempo_de_contribuicao or "",
            "autuacao_processo": Tools.FormatarData(proc.autuacao_processo),
            "data_atual": Tools.DataAtual(),
            "folha_ato_concessorio": proc.folha_ato_concessorio or "",
            "folha_ato_fixacao": proc.folha_ato_fixacao or "",
            "tipo": proc.classe.descricao.title() if proc.classe else "Aposentadoria",
            "data_inicio_concessao": Tools.FormatarData(proc.data_inicio_concessao),
            "dados_previdencia": proc.dados_previdencia or ""
        }
        return dados
        
    