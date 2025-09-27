from __future__ import print_function
import base64
import os.path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Escopo necessário para enviar emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def autenticar_gmail():
    """Autentica com a API do Gmail e retorna o serviço."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def criar_mensagem_com_anexo(destinatario, assunto, mensagem_texto, caminho_anexo):
    """Cria a mensagem de e-mail com anexo."""
    # Cria a estrutura de e-mail
    message = MIMEMultipart()
    message['to'] = destinatario
    message['subject'] = assunto

    # Corpo do e-mail
    message.attach(MIMEText(mensagem_texto, 'plain'))

    # Anexo
    if caminho_anexo:
        with open(caminho_anexo, 'rb') as f:
            mime_base = MIMEBase('application', 'octet-stream')
            mime_base.set_payload(f.read())
        encoders.encode_base64(mime_base)
        mime_base.add_header(
            'Content-Disposition',
            f'attachment; filename="{os.path.basename(caminho_anexo)}"'
        )
        message.attach(mime_base)

    # Converte para base64
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

def enviar_email(service, destinatario, assunto, mensagem_texto, caminho_anexo=None):
    """Envia o e-mail usando a API Gmail."""
    mensagem = criar_mensagem_com_anexo(destinatario, assunto, mensagem_texto, caminho_anexo)
    enviado = service.users().messages().send(userId="me", body=mensagem).execute()
    print(f"E-mail enviado! ID da mensagem: {enviado['id']}")

if __name__ == '__main__':
    service = autenticar_gmail()
    enviar_email(
        service,
        destinatario="destino@email.com",
        assunto="Teste com Anexo via Gmail API",
        mensagem_texto="Olá, este é um e-mail enviado pela API Gmail com Python e contém um anexo!"
    )
