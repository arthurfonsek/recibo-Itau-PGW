import json
import os
import base64
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
import re
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('email_service')

# Email configuration

EMAIL_FROM = os.environ['EMAIL_FROM']
SMTP_SERVER = os.environ['SMTP_SERVER']
SMTP_PORT = int(os.environ['SMTP_PORT'])
SMTP_USERNAME = os.environ['SMTP_USERNAME']
SMTP_PASSWORD = os.environ['SMTP_PASSWORD']

def parse_datetime(date_str):
    """Parse datetime from the format in the JSON."""
    # Format: 2025-03-31-15.36.49.637000
    date_parts = date_str.split('-')
    year = date_parts[0]
    month = date_parts[1]
    day = date_parts[2]
    
    # Convert month number to month name in Portuguese
    month_names = {
        '01': 'janeiro',
        '02': 'fevereiro',
        '03': 'março',
        '04': 'abril',
        '05': 'maio',
        '06': 'junho',
        '07': 'julho',
        '08': 'agosto',
        '09': 'setembro',
        '10': 'outubro',
        '11': 'novembro',
        '12': 'dezembro'
    }
    
    month_name = month_names.get(month, month)
    
    time = date_parts[3].replace('.', ':')
    time = ':'.join(time.split(':')[:3])  # Get only HH:MM:SS
    
    # Return formatted date components for more flexibility
    return day, month_name, year, time

def generate_pdf(data, output_file="/tmp/recibo.pdf"):
    """Generate a PDF receipt based on the provided data in Itaú style."""
    print("Starting PDF generation...")
    
    # List contents of current directory and /tmp for debugging
    print("Current directory contents:", os.listdir('.'))
    print("/tmp directory contents:", os.listdir('/tmp'))
    
    doc = SimpleDocTemplate(output_file, pagesize=letter, 
                            leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor('#4a4746')
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=colors.HexColor('#4a4746'),
        spaceBefore=6,
        spaceAfter=2
    )
    
    subheader_style = ParagraphStyle(
        'SubheaderStyle',
        parent=styles['Heading3'],
        fontSize=9,
        textColor=colors.HexColor('#4a4746'),
        spaceBefore=4,
        spaceAfter=2
    )
    
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=3,
        textColor=colors.HexColor('#4a4746')
    )
    
    italic_style = ParagraphStyle(
        'ItalicStyle',
        parent=styles['Italic'],
        fontSize=10,
        textColor=colors.HexColor('#4a4746')
    )
    
    important_note_style = ParagraphStyle(
        'ImportantNoteStyle',
        parent=styles['Italic'],
        fontSize=11,
        textColor=colors.HexColor('#4a4746'),
        alignment=TA_CENTER,
        spaceBefore=2,
        spaceAfter=2
    )
    
    # Extract payment data
    payment_data = data['data']['dados_pagamento']
    pix_data = payment_data.get('dados_pix_transferencia', {})
    
    # Find the efetivação status to get transaction date and time
    transaction_date = ""
    transaction_time = ""
    day = ""
    month = ""
    year = ""
    time = ""
    for entry in data['data']['historico_pagamento']:
        if entry['status'] == 'Efetivação':
            day, month, year, time = parse_datetime(entry['data'])
            break
    
    # Content elements
    elements = []
    
    # Add logo
    original_logo_path = "LOGO COLORIDO FUNDO TRANSPARENTE.png"
    tmp_logo_path = "/tmp/logo.png"
    
    print(f"Checking for logo at original path: {original_logo_path}")
    print(f"Original logo exists: {os.path.exists(original_logo_path)}")
    
    # Copy logo to /tmp if it exists
    if os.path.exists(original_logo_path):
        print("Found logo in original location, copying to /tmp...")
        try:
            import shutil
            shutil.copy2(original_logo_path, tmp_logo_path)
            print("Logo copied successfully to /tmp")
        except Exception as e:
            print(f"Error copying logo to /tmp: {str(e)}")
    
    # Try to use the logo from either location
    logo_path = tmp_logo_path if os.path.exists(tmp_logo_path) else original_logo_path
    print(f"Using logo path: {logo_path}")
    print(f"Logo file exists at final path: {os.path.exists(logo_path)}")
    
    if os.path.exists(logo_path):
        try:
            print("Attempting to create Image object...")
            # Create Image object with controlled size
            logo = Image(logo_path)
            
            # Set a fixed width
            desired_width = 1.5 * inch
            
            # Calculate height maintaining aspect ratio
            aspect_ratio = logo.imageHeight / logo.imageWidth
            desired_height = desired_width * aspect_ratio
            
            logo.drawWidth = desired_width
            logo.drawHeight = desired_height
            
            # Use horizontal alignment for the logo (Itaú style - logo at left)
            logo_table = Table(
                [[logo]], 
                colWidths=[letter[0] - 60],  # full width minus margins
                rowHeights=[desired_height]
            )
            logo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            print("Logo image object created successfully")
            elements.append(logo_table)
            print("Logo added to elements list")
            
            # Add more space after the logo
            elements.append(Spacer(1, 0.3 * inch))  # Increased spacing here
        except Exception as e:
            print(f"Error adding logo to PDF: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full error traceback: {traceback.format_exc()}")
    else:
        print("Logo file not found in any location")
    
    # Add document title
    elements.append(Paragraph("COMPROVANTE DE TRANSFERÊNCIA", title_style))
    
    # Add thin line
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#4a4746'), spaceAfter=0.1*inch))
    elements.append(Spacer(1, 0.05 * inch))
    
    # Add Itaú-style transaction header
    if day and month and year and time:
        transaction_info = f"Transação efetuada em {day} de {month}, {year} às {time} via Sispag"
    else:
        transaction_info = "Transação efetuada via Sispag"
    elements.append(Paragraph(transaction_info, italic_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Create a 2-column table for payer information (Itaú style)
    payer_data = [
        [Paragraph("<b>DADOS DO PAGADOR</b>", header_style), ""],
        [Paragraph("<b>Nome:</b>", normal_style), Paragraph("PGW PAYMENTS INTERNET LTDA", normal_style)],
        [Paragraph("<b>CNPJ:</b>", normal_style), Paragraph("33.392.629/0001-83", normal_style)],
        [Paragraph("<b>Conta:</b>", normal_style), Paragraph("7633/16677-7", normal_style)]
    ]
    
    payer_table = Table(payer_data, colWidths=[1.5*inch, 4.0*inch])
    payer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(payer_table)
    
    # Separator
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#4a4746'), spaceAfter=0.1*inch))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Create a 2-column table for receiver information (Itaú style)
    receiver_data = [
        [Paragraph("<b>DADOS DO RECEBEDOR</b>", header_style), ""],
        [Paragraph("<b>Nome:</b>", normal_style), Paragraph(payment_data['nome_favorecido'], normal_style)],
        [Paragraph("<b>Chave PIX:</b>", normal_style), Paragraph(pix_data.get('chave_enderecamento', ''), normal_style)],
        [Paragraph("<b>CPF/CNPJ:</b>", normal_style), Paragraph(payment_data['cpf_cnpj_favorecido'], normal_style)]
    ]
    
    receiver_table = Table(receiver_data, colWidths=[1.5*inch, 4.0*inch])
    receiver_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(receiver_table)
    
    # Separator
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#4a4746'), spaceAfter=0.1*inch))
    elements.append(Spacer(1, 0.1 * inch))
    
    # Create a 2-column table for payment details (Itaú style)
    payment_details = [
        [Paragraph("<b>DADOS DO PAGAMENTO</b>", header_style), ""],
        [Paragraph("<b>Valor:</b>", normal_style), Paragraph(f"R$ {payment_data['valor_pagamento']}", normal_style)],
        [Paragraph("<b>Data:</b>", normal_style), Paragraph(payment_data['data_pagamento'], normal_style)],
        [Paragraph("<b>Tipo:</b>", normal_style), Paragraph(payment_data['tipo_pagamento_descricao'], normal_style)]
    ]
    
    # Add company reference if available
    if payment_data.get('referencia_empresa'):
        payment_details.append([Paragraph("<b>Pagador:</b>", normal_style), Paragraph(payment_data.get('referencia_empresa', ''), normal_style)])
    
    # Add authorization code if available
    if payment_data.get('comprovante'):
        payment_details.append([Paragraph("<b>Nº do comprovante:</b>", normal_style), Paragraph(payment_data.get('comprovante', ''), normal_style)])
    
    # Add message to receiver here (after comprovante)
    if pix_data.get('mensagem_ao_recebedor'):
        payment_details.append([Paragraph("<b>Mensagem:</b>", normal_style), Paragraph(pix_data.get('mensagem_ao_recebedor', ''), normal_style)])
    
    payment_table = Table(payment_details, colWidths=[1.5*inch, 4.0*inch])
    payment_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(payment_table)
    
    # Add Itaú footer
    elements.append(Spacer(1, 0.3 * inch))
    
    # Create a table with white background for the important message
    important_message = Paragraph("Importante: A PGW Payments utilizou a plataforma do BANCO ITAÚ no processamento desta transação.", important_note_style)
    
    message_table = Table(
        [[important_message]], 
        colWidths=[letter[0] - 60]  # full width minus margins
    )
    message_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.white),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
        ('TOPPADDING', (0, 0), (0, 0), 15),
        ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor('#4a4746')),
        ('LINEBELOW', (0, 0), (0, 0), 1, colors.HexColor('#4a4746')),
    ]))
    
    elements.append(message_table)
    
    print("Building final PDF...")
    # Build the PDF
    doc.build(elements)
    print("PDF built successfully")
    
    # Clean up the temporary logo file
    if os.path.exists(tmp_logo_path):
        try:
            os.remove(tmp_logo_path)
            print("Temporary logo file cleaned up")
        except Exception as e:
            print(f"Error cleaning up temporary logo: {str(e)}")
            
    return output_file

def is_valid_email(email):
    """Validate email format using regex."""
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def send_email(to_email, subject, body, pdf_content=None):
    """
    Send email with improved error handling and delivery verification.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): HTML email body
        pdf_content (bytes, optional): PDF content to attach
        
    Returns:
        dict: Status information including message_id for tracking
    """
    # Generate a unique message ID for tracking
    message_id = f"<{uuid.uuid4()}@pgwpay.com.br>"
    
    # Validate recipient email
    if not is_valid_email(to_email):
        error_msg = f"Invalid email address: {to_email}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'message_id': None,
            'recipient': to_email,
            'error_type': 'INVALID_EMAIL'
        }
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['Message-ID'] = message_id
    
    # Request Delivery Status Notifications
    msg['Return-Path'] = EMAIL_FROM
    msg['Disposition-Notification-To'] = EMAIL_FROM  # Read receipt request
    
    # Add HTML body
    msg.attach(MIMEText(body, 'html'))

    # Add PDF attachment if provided
    if pdf_content:
        pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', filename='recibo.pdf')
        msg.attach(pdf_attachment)

    # Detailed error handling
    try:
        logger.info(f"Initiating email send to {to_email} with message ID: {message_id}")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            logger.info(f"Connected to SMTP server: {SMTP_SERVER}")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            logger.info("SMTP authentication successful")
            
            # Send the message
            response = server.send_message(msg)
            
            # Check if there were any rejected recipients
            if response:
                rejected_recipients = list(response.keys())
                logger.error(f"Failed to deliver to some recipients: {rejected_recipients}")
                return {
                    'success': False,
                    'message': f"Email rejected for recipients: {', '.join(rejected_recipients)}",
                    'message_id': message_id,
                    'recipient': to_email,
                    'error_type': 'RECIPIENT_REJECTED'
                }
            
            logger.info(f"Email sent successfully to {to_email}")
            return {
                'success': True,
                'message': "Email sent successfully",
                'message_id': message_id,
                'recipient': to_email,
                'error_type': None
            }
            
    except smtplib.SMTPRecipientsRefused as e:
        error_msg = f"All recipients refused: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'message_id': message_id,
            'recipient': to_email,
            'error_type': 'RECIPIENTS_REFUSED'
        }
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication Error: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'message_id': message_id,
            'recipient': to_email,
            'error_type': 'AUTH_ERROR'
        }
        
    except smtplib.SMTPConnectError as e:
        error_msg = f"SMTP Connection Error: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'message_id': message_id,
            'recipient': to_email,
            'error_type': 'CONNECTION_ERROR'
        }
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP Error: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg,
            'message_id': message_id,
            'recipient': to_email,
            'error_type': 'SMTP_ERROR'
        }
        
    except Exception as e:
        error_msg = f"Unexpected error sending email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'message': error_msg,
            'message_id': message_id,
            'recipient': to_email,
            'error_type': 'UNEXPECTED_ERROR'
        }

def lambda_handler(event, context):
    """AWS Lambda function handler"""
    try:
        logger.info("Lambda function started")
        logger.info(f"Event received: {json.dumps(event)}")
        
        # Check if the event contains a body
        if 'body' in event:
            # If the body is a string (from API Gateway), parse it
            if isinstance(event['body'], str):
                data = json.loads(event['body'])
            else:
                data = event['body']
        else:
            # If no body, assume the event itself is the JSON data
            data = event
        
        logger.info(f"Processing data for email: {data.get('email')}")
        
        # Generate the PDF
        logger.info("Generating PDF...")
        pdf_path = generate_pdf(data)
        logger.info(f"PDF generated at: {pdf_path}")
        
        # Read the PDF file and encode it as base64 for the response
        logger.info("Reading PDF file for base64 encoding...")
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Get email from the data
        recipient_email = data.get('email')
        
        # Send email with PDF attachment if email is provided
        email_response = None
        if recipient_email:
            logger.info(f"Preparing to send email to: {recipient_email}")
            # Create a temporary copy of the PDF for email
            temp_pdf_path = "/tmp/email_recibo.pdf"
            with open(temp_pdf_path, 'wb') as temp_file:
                temp_file.write(pdf_content)
            
            # Safely get payment data with defaults
            payment_data = data.get('data', {}).get('dados_pagamento', {})
            nome_favorecido = payment_data.get('nome_favorecido', '')
            valor_pagamento = payment_data.get('valor_pagamento', '')
            razao_social = payment_data.get('razao_social', '')
            autorizacao = payment_data.get('autorizacao', '')
            cpf_cnpj_favorecido = payment_data.get('cpf_cnpj_favorecido', '')
            referencia_empresa = payment_data.get('referencia_empresa', '')
            descricao = payment_data.get('descricao', '')
            
            # Get PIX data
            pix_data = payment_data.get('dados_pix_transferencia', {})
            chave_pix = pix_data.get('chave_enderecamento', '')
            mensagem_recebedor = pix_data.get('mensagem_ao_recebedor', '')
            
            # Create the email message
            msg = MIMEMultipart('related')
            msg['From'] = EMAIL_FROM
            msg['To'] = recipient_email
            msg['Subject'] = f"Comprovante de Pagamento - {nome_favorecido}"
            
            # Add HTML body
            html_body = f'''
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Comprovante de Pagamento</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                    <!-- Cabeçalho -->
                    <tr>
                        <td style="background-color: #546375; text-align: center; padding: 20px 0;">
                            <div style="background-color: #ffffff; display: inline-block; padding: 10px; border-radius: 5px;">
                                <img src="cid:logo" alt="PGW Logo" height="80" style="display: block;">
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Conteúdo -->
                    <tr>
                        <td style="padding: 30px 40px;">
                            <h1 style="color: #4a4746; font-size: 22px; margin: 0 0 20px; text-align: center;">Comprovante de Pagamento</h1>
                            
                            <p style="margin: 0 0 20px; font-size: 14px; color: #333333; line-height: 1.5;">
                                Prezado cliente,
                            </p>
                            
                            <p style="margin: 0 0 20px; font-size: 14px; color: #333333; line-height: 1.5;">
                                O pagamento de <strong style="color: #000;">R$ {valor_pagamento}</strong> solicitado por <strong style="color: #000;">{referencia_empresa}</strong> foi efetivado com sucesso. Seguem as informações do pagamento:
                            </p>
                            
                            <!-- Detalhes do Pagamento -->
                            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin: 20px 0; border-collapse: collapse; border: 1px solid #e0e0e0; border-radius: 4px;">
                                <tr>
                                    <td style="background-color: #f9f9f9; padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-weight: bold;" colspan="2">
                                        Detalhes da Transação
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; width: 40%; font-weight: bold; color: #4a4746;">
                                        Recebedor:
                                    </td>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; color: #333333;">
                                        {nome_favorecido}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #4a4746;">
                                        Chave PIX utilizada:
                                    </td>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; color: #333333;">
                                        {chave_pix}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #4a4746;">
                                        CPF/CNPJ:
                                    </td>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; color: #333333;">
                                        {cpf_cnpj_favorecido}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #4a4746;">
                                        Valor:
                                    </td>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #333333;">
                                        R$ {valor_pagamento}
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: #4a4746;">
                                        Descrição:
                                    </td>
                                    <td style="padding: 10px 15px; border-bottom: 1px solid #e0e0e0; color: #333333;">
                                        {mensagem_recebedor}
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 25px 0; font-size: 14px; color: #333333; line-height: 1.5; font-style: italic; text-align: center;">
                                O comprovante de pagamento está anexo a este e-mail.
                            </p>
                            
                            <div style="background-color: #f9f9f9; border: 1px solid #e0e0e0; border-radius: 4px; padding: 15px; margin: 20px 0; text-align: center;">
                                <p style="margin: 0; font-size: 14px; color: #4a4746; font-style: italic;">
                                    Importante: A PGW Payments utilizou a plataforma do BANCO ITAÚ no processamento desta transação.
                                </p>
                            </div>
                            
                            <p style="margin: 20px 0 0; font-size: 12px; color: #666666; font-style: italic;">
                                Este e-mail foi enviado automaticamente pelo sistema de pagamentos PGW. Por favor, não responda a este e-mail.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Rodapé -->
                    <tr>
                        <td style="background-color: #f1f1f1; padding: 30px; text-align: center;">
                            <p style="margin: 0 0 15px; font-size: 14px; color: #333333;">
                                Caso tenha qualquer dúvida, entre em contato conosco:
                                <a href="mailto:contato@pgwpay.com.br" style="color: #0066cc; text-decoration: none;">contato@pgwpay.com.br</a>
                            </p>
                            
                            <img src="cid:logo_footer" height="50" style="display: inline-block; margin-bottom: 15px;" alt="PGW Logo">
                            
                            <p style="margin: 0 0 5px; font-size: 12px; color: #666666;">
                                <a href="https://www.pgwpay.com.br" style="color: #0066cc; text-decoration: none;">www.pgwpay.com.br</a>
                            </p>
                            
                            <p style="margin: 0 0 5px; font-size: 12px; color: #666666;">
                                Rua Aurora, 817 | 8º andar | São Paulo | SP
                            </p>
                            
                            <p style="margin: 0 0 15px; font-size: 12px; color: #666666;">
                                © 2023 | Todos os direitos reservados a PGW PAYMENTS INTERNET LTDA.<br>
                                CNPJ: 33.392.629/0001-83
                            </p>
                            
                            <div style="margin-top: 10px;">
                                <a href="https://www.facebook.com/pgwpay" style="display: inline-block; margin: 0 5px;"><img src="https://cdn-icons-png.flaticon.com/32/733/733547.png" width="24" alt="Facebook"></a>
                                <a href="https://www.instagram.com/pgwpay" style="display: inline-block; margin: 0 5px;"><img src="https://cdn-icons-png.flaticon.com/32/1384/1384063.png" width="24" alt="Instagram"></a>
                                <a href="https://www.linkedin.com/company/pgwpay" style="display: inline-block; margin: 0 5px;"><img src="https://cdn-icons-png.flaticon.com/32/3536/3536505.png" width="24" alt="LinkedIn"></a>
                            </div>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            '''
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Attach the logo images
            logo_path = "LOGO COLORIDO FUNDO TRANSPARENTE.png"
            if os.path.exists(logo_path):
                # Attach header logo
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                    img = MIMEImage(logo_data)
                    img.add_header('Content-ID', '<logo>')
                    img.add_header('Content-Disposition', 'inline')
                    msg.attach(img)
                
                # Attach footer logo (reading file again)
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                    footer_img = MIMEImage(logo_data)
                    footer_img.add_header('Content-ID', '<logo_footer>')
                    footer_img.add_header('Content-Disposition', 'inline')
                    msg.attach(footer_img)
            
            # Attach PDF
            pdf_attachment = MIMEApplication(pdf_content, _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename='recibo.pdf')
            msg.attach(pdf_attachment)
            
            # Send email
            try:
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.send_message(msg)
                email_response = {
                    'success': True, 
                    'message': "Email sent successfully",
                    'recipient': recipient_email
                }
                logger.info(f"Email sent successfully to {recipient_email}")
            except Exception as e:
                error_msg = f"Error sending email: {str(e)}"
                logger.error(error_msg, exc_info=True)
                email_response = {
                    'success': False, 
                    'message': error_msg,
                    'recipient': recipient_email
                }
            
            # Clean up the temporary PDF file
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
        else:
            logger.info("No email provided, skipping email sending")
            email_response = {
                'success': False,
                'message': "No recipient email provided", 
                'recipient': None
            }
        
        # Create response
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'PDF gerado e e-mail enviado com sucesso',
                'email_sent': email_response and email_response.get('success', False),
                'email_recipient': recipient_email if recipient_email else 'Não fornecido',
                'email_response': email_response,
                'pdf_base64': pdf_base64
            })
        }
        
        logger.info("Lambda function completed successfully")
        return response
        
    except Exception as e:
        error_msg = f"Error in lambda_handler: {str(e)}"
        logger.error(error_msg, exc_info=True)
        # Return error response
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg
            })
        }
