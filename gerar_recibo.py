import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def parse_datetime(date_str):
    """Parse datetime from the format in the JSON."""
    # Format: 2025-03-31-15.36.49.637000
    date_parts = date_str.split('-')
    date = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
    time = date_parts[3].replace('.', ':')
    time = ':'.join(time.split(':')[:3])  # Get only HH:MM:SS
    return date, time

def generate_pdf(data, output_file="recibo.pdf"):
    """Generate a PDF receipt based on the provided data."""
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    
    # Extract payment data
    payment_data = data['data']['dados_pagamento']
    pix_data = payment_data.get('dados_pix_transferencia', {})
    
    # Find the efetivação status to get transaction date and time
    transaction_date = ""
    transaction_time = ""
    for entry in data['data']['historico_pagamento']:
        if entry['status'] == 'Efetivação':
            transaction_date, transaction_time = parse_datetime(entry['data'])
            break
    
    # Get institution name from the receiver's information
    # Since it's not available in the JSON, we're leaving it blank
    institution = ""
    
    # Content elements
    elements = []
    
    # Title
    elements.append(Paragraph("COMPROVANTE DE PAGAMENTO", title_style))
    elements.append(Spacer(1, 12))
    
    # Separator line
    elements.append(Paragraph("-" * 55, normal_style))
    
    # Payer information (fixed)
    elements.append(Paragraph("DADOS DO PAGADOR", section_style))
    elements.append(Paragraph("Nome do pagador: PGW PAYMENTS INTERNET LTDA", normal_style))
    elements.append(Paragraph("CNPJ do pagador: 33.392.629/0001-83", normal_style))
    elements.append(Paragraph("Agência/conta: 7633/16677-7", normal_style))
    
    # Separator line
    elements.append(Paragraph("-" * 55, normal_style))
    
    # Receiver information
    elements.append(Paragraph("DADOS DO RECEBEDOR", section_style))
    elements.append(Paragraph(f"Nome do recebedor: {payment_data['nome_favorecido']}", normal_style))
    elements.append(Paragraph(f"Chave: {pix_data.get('chave_enderecamento', '')}", normal_style))
    elements.append(Paragraph(f"CPF/CNPJ do recebedor: {payment_data['cpf_cnpj_favorecido']}", normal_style))
    elements.append(Paragraph(f"Instituição: {institution}", normal_style))
    elements.append(Paragraph(f"Mensagem ao recebedor: {pix_data.get('mensagem_ao_recebedor', '')}", normal_style))
    elements.append(Paragraph(f"Identificação no comprovante: {payment_data.get('referencia_empresa', '')}", normal_style))
    
    # Separator line
    elements.append(Paragraph("-" * 55, normal_style))
    
    # Payment details
    elements.append(Paragraph(f"Valor: R$ {payment_data['valor_pagamento']}", normal_style))
    elements.append(Paragraph(f"Data da transferência: {payment_data['data_pagamento']}", normal_style))
    elements.append(Paragraph(f"Tipo de pagamento: {payment_data['tipo_pagamento_descricao']}", normal_style))
    
    # Separator line
    elements.append(Paragraph("-" * 55, normal_style))
    
    # Transaction footer
    elements.append(Paragraph(f"Transação efetuada em {transaction_date} às {transaction_time} via Sispag.", normal_style))
    
    # Build the PDF
    doc.build(elements)
    return output_file

def main():
    """Main function to process the input and generate the PDF."""
    # Example usage with the provided JSON
    json_data = {
        "email": "arthur.b.dafonseca@gmail.com",
        "data": {
            "dados_debito": {
                "numero_agencia_debito": "7633",
                "numero_conta_debito": "00166777",
                "nome_empresa_debito": "PGW PAYMENTS INTERNET LTDA",
                "cnpj_debito": "33392629000183"
            },
            "dados_pagamento": {
                "id_pagamento": "a3649c0c-372a-4aa7-b1ce-8f0629e1d2ec",
                "cod_tipo_pessoa": "J",
                "cpf_cnpj_favorecido": "66943820000125",
                "nome_favorecido": "POLICROM GALVANOTECNICA LTD...",
                "valor_pagamento": "680.00",
                "numero_lote": "146166898",
                "numero_lancamento": "56683",
                "referencia_empresa": "SGI POWER TRANSMISSI",
                "data_pagamento": "2025-03-31",
                "status": "Efetuado",
                "comprovante": "00434176330016677700002100120250331146166898056683",
                "codigo_isbp": "54401286",
                "tipo_pagamento": "45",
                "tipo_pagamento_descricao": "PIX Transferências",
                "motivo_rejeicao": [],
                "dados_pix_transferencia": {
                    "chave_enderecamento": "66943820000125",
                    "mensagem_ao_recebedor": "Pago por conta e ordem de SGI POWER TRANSMISSION DO BRASIL LTDA | CNPJ 18.299.985/0001-63"
                },
                "valor_tarifa_transferencia": 0.74
            },
            "historico_pagamento": [
                {
                    "status": "Inclusão - API Externa",
                    "data": "2025-03-31-09.10.46.603000",
                    "cod_operador": "0"
                },
                {
                    "status": "Autorização",
                    "data": "2025-03-31-09.21.04.750000",
                    "nome_operador": "LUIZ CARLOS PASSAFARO GRANDE",
                    "cod_operador": "831910842",
                    "cpf_operador": "08364130838"
                },
                {
                    "status": "Autorização",
                    "data": "2025-03-31-15.36.49.283000",
                    "nome_operador": "LUIZ CARLOS PASSAFARO GRANDE",
                    "cod_operador": "831910842",
                    "cpf_operador": "08364130838"
                },
                {
                    "status": "Efetivação",
                    "data": "2025-03-31-15.36.49.637000",
                    "cod_operador": "0"
                }
            ]
        }
    }
    
    # In a real application, you might load the JSON from a file or receive it from an API
    # json_data = json.loads(input_json_str)
    
    pdf_file = generate_pdf(json_data)
    print(f"PDF receipt generated: {pdf_file}")

if __name__ == "__main__":
    main() 