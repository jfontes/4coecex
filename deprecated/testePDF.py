from leitorPDF import LeitorPDF

leitor = LeitorPDF()
try:
    texto = leitor.extrair_texto("C:\\projetos\\certificador\\teste3.pdf")
    print(texto)
except Exception as e:
    print(f"Ocorreu um erro: {e}")