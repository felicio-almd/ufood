import json
import os
from datetime import datetime, timedelta

import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_ufes_menu():
    amanha = datetime.now() + timedelta(days=1)
    data_str = amanha.strftime("%Y-%m-%d")

    url = f"https://restaurante.saomateus.ufes.br/cardapio/{data_str}"

    try:
        response = requests.get(url, timeout=15, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="view-content")

        if not content:
            return {"error": f"Cardápio não disponível para {data_str}", "url": url}

        cardapio = {
            "data": amanha.strftime("%d/%m/%Y"),
            "url_fonte": url,
            "refeicoes": [],
        }

        titulos = content.find_all("div", class_="views-field-title")

        for titulo_div in titulos:
            nome = titulo_div.get_text(strip=True)

            parent = titulo_div.parent
            body_div = parent.find("div", class_="views-field-body")

            itens = {}
            if body_div:
                paragrafos = body_div.find_all("p")
                chave_atual = None

                for p in paragrafos:
                    strong = p.find("strong")

                    if strong:
                        chave_atual = strong.get_text(strip=True).replace(":", "")
                    elif chave_atual:
                        valor = p.get_text(strip=True).replace("\xa0", "")

                        if valor and "O cardápio poderá sofrer alterações" not in valor:
                            if chave_atual in itens:
                                itens[chave_atual] += f" | {valor}"
                            else:
                                itens[chave_atual] = valor

            cardapio["refeicoes"].append({"titulo": nome, "itens": itens})

        return cardapio

    except Exception as e:
        return {"error": str(e)}


def formatar_mensagem(dados_cardapio):
    if "error" in dados_cardapio:
        return f"❌ *Erro ao buscar o cardápio da UFES:*\n{dados_cardapio['error']}"

    refeicoes = dados_cardapio.get("refeicoes", [])
    if not refeicoes:
        return f"⚠️ O cardápio para o dia {dados_cardapio.get('data')} ainda não foi publicado no site."

    msg = f"🍽️ *CARDÁPIO RU CEUNES - {dados_cardapio['data']}* 🍽️\n\n"

    for refeicao in refeicoes:
        titulo_limpo = refeicao["titulo"].split("-")[0].strip()
        msg += f"🍲 *{titulo_limpo}*\n"

        for chave, valor in refeicao["itens"].items():
            msg += f"• *{chave}:* {valor}\n"

        msg += "\n"  #

    return msg


# --- NOVA FUNÇÃO 2: Enviar para o WhatsApp ---
def enviar_mensagem(mensagem, grupo_id):
    """
    Envia a mensagem via requisição POST para uma API do WhatsApp.
    """
    api_url = os.environ.get(
        "WHATSAPP_API_URL", "http://sua-vps-ip:porta/message/sendText/sua_instancia"
    )
    api_key = os.environ.get("WHATSAPP_API_KEY", "sua_chave_aqui")

    headers = {"Content-Type": "application/json", "apikey": api_key}

    payload = {"number": grupo_id, "textMessage": {"text": mensagem}}

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        print("✅ Mensagem enviada com sucesso para o WhatsApp!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar para o WhatsApp: {e}")
        return False

def enviar_mensagem_telegram(mensagem):
    import os
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "XXXXXXXXXXXXXXXX")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "XXXXXXXXXXXX")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Mensagem enviada com sucesso para o Telegram!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao enviar para o Telegram: {e}")
        # Se der erro 400, a API do Telegram retorna detalhes do motivo
        if e.response is not None:
            print(f"Detalhes: {e.response.text}")
        return False

if __name__ == "__main__":
    print("Buscando dados no site da UFES...")
    dados = fetch_ufes_menu()

    texto_formatado = formatar_mensagem(dados)
    print("\n--- Mensagem que será enviada ---")
    print(texto_formatado)
    print("---------------------------------\n")

    # 2. Envia para o WhatsApp (Descomente quando tiver a API configurada)
    # ID de grupo no WhatsApp geralmente termina com @g.us (ex: 120363000000000000@g.us)
    # ID_DO_GRUPO = "COLOQUE_O_ID_AQUI@g.us"
    # enviar_mensagem(texto_formatado, ID_DO_GRUPO)

    # Envia pro Telegram
    enviar_mensagem_telegram(texto_formatado)
