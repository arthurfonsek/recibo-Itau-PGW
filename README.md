# Gerador de Recibo - AWS Lambda

Este projeto contém uma função AWS Lambda que gera um comprovante de pagamento em formato PDF a partir de dados JSON e envia por e-mail para o destinatário usando SendGrid.

## Arquivos

- `main.py`: Função principal AWS Lambda
- `documentacao_recibo.py`: Gerador de documentação do sistema
- `gerar_documentacao.py`: Script para gerar o PDF de documentação
- `email_diagnostics.py`: Ferramenta de diagnóstico de envio de emails
- `requirements.txt`: Dependências do projeto
- `README_EMAIL.md`: Documentação detalhada sobre o sistema de email

## Funcionalidades

- Gera um PDF com comprovante de pagamento formatado
- Envia o PDF como anexo por e-mail para o destinatário usando SendGrid
- Retorna o PDF codificado em base64 na resposta da API
- Valida endereços de email e verifica a entrega
- Fornece logging detalhado do processo de envio 
- Inclui ferramenta de diagnóstico para verificação do sistema de email

## Configuração e Implantação

### Pré-requisitos

- AWS CLI configurada
- Python 3.8 ou superior
- Uma conta AWS com permissões para criar funções Lambda
- Conta SendGrid com API Key configurada
- Biblioteca dnspython para a ferramenta de diagnóstico

### Instalação de Dependências

```bash
pip install -r requirements.txt
```

### Criação do Pacote de Implantação

1. Crie uma pasta para as dependências:
```bash
mkdir -p package
pip install -r requirements.txt --target ./package
```

2. Copie o código da função para o pacote:
```bash
cp main.py package/
```

3. Crie o arquivo ZIP para implantação:
```bash
cd package
zip -r ../lambda_function.zip .
cd ..
```

### Implantação na AWS

Use o console AWS ou o AWS CLI para implantar a função:

```bash
aws lambda create-function \
    --function-name GeradorRecibo \
    --runtime python3.8 \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
    --handler main.lambda_handler \
    --zip-file fileb://lambda_function.zip
```

## Uso

A função Lambda pode ser invocada diretamente com um payload JSON ou através de um endpoint API Gateway.

### Formato do Payload

O payload deve seguir o formato:

```json
{
    "email": "usuario@exemplo.com",
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
            "nome_favorecido": "EMPRESA EXEMPLO",
            "valor_pagamento": "680.00",
            "numero_lote": "146166898",
            "numero_lancamento": "56683",
            "referencia_empresa": "REFERENCIA",
            "data_pagamento": "2025-03-31",
            "status": "Efetuado",
            "comprovante": "00434176330016677700002100120250331146166898056683",
            "codigo_isbp": "54401286",
            "tipo_pagamento": "45",
            "tipo_pagamento_descricao": "PIX Transferências",
            "motivo_rejeicao": [],
            "dados_pix_transferencia": {
                "chave_enderecamento": "66943820000125",
                "mensagem_ao_recebedor": "Mensagem de exemplo"
            },
            "valor_tarifa_transferencia": 0.74
        },
        "historico_pagamento": [
            {
                "status": "Efetivação",
                "data": "2025-03-31-15.36.49.637000",
                "cod_operador": "0"
            }
        ]
    }
}
```

### Resposta

A resposta será um JSON contendo:
- Status do envio de e-mail
- Destinatário do e-mail
- Resposta detalhada do sistema de envio
- PDF codificado em base64

## Verificação de Emails

Este projeto inclui uma ferramenta de diagnóstico para verificar o sistema de envio de emails. Para usá-la:

```bash
# Verificar a conexão com o servidor SMTP
python3 email_diagnostics.py --check-connection

# Verificar registros DNS de um domínio de email
python3 email_diagnostics.py --check-dns exemplo.com.br

# Enviar um email de teste
python3 email_diagnostics.py --send-test usuario@exemplo.com.br
```

Para mais detalhes sobre a verificação de emails, consulte o arquivo [README_EMAIL.md](README_EMAIL.md). 