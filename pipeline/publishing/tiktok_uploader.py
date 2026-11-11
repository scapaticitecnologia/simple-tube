"""
Simple-Tube TikTok Uploader
Faz upload automático de vídeos no TikTok Creator Center (creator.tiktok.com)
usando Playwright com persistência de sessão e proteção anti-bot.
"""

import os
import sys
import json
import time
import argparse
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(SCRIPT_DIR, "tiktok_session.json")

def get_browser_instance(p, headless=False):
    """Lança o navegador com modo stealth para evitar bloqueios do TikTok."""
    args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-infobars",
        "--start-maximized"
    ]
    try:
        # Tenta usar o Microsoft Edge nativo do Windows (menor chance de ser sinalizado)
        return p.chromium.launch(
            channel="msedge",
            headless=headless,
            args=args,
            ignore_default_args=["--enable-automation"]
        )
    except Exception:
        return p.chromium.launch(
            headless=headless,
            args=args,
            ignore_default_args=["--enable-automation"]
        )

def set_session_cookie(session_id: str):
    """Configura a sessão diretamente a partir do cookie sessionid fornecido pelo usuário."""
    clean_sid = session_id.strip().strip('"').strip("'")
    if not clean_sid:
        print("[TIKTOK] ❌ Valor do sessionid inválido.")
        return False

    cookies = [
        {
            "name": "sessionid",
            "value": clean_sid,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        },
        {
            "name": "sessionid_ss",
            "value": clean_sid,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        },
        {
            "name": "sid_tt",
            "value": clean_sid,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "None"
        }
    ]

    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"cookies": cookies, "origins": []}, f, indent=2)

    print(f"[TIKTOK] ✅ Sessão gerada com sucesso a partir do sessionid em: {SESSION_FILE}")
    return True

def setup_session():
    """Abre o navegador oficial para login único e detecta o cookie de autenticação."""
    print("\n" + "=" * 60)
    print("🎵 SETUP DO TIKTOK CREATOR CENTER (LOGIN ÚNICO)")
    print("=" * 60)
    print("Uma janela limpa do navegador está se abrindo no TikTok.")
    print("Faça o login na conta do canal Scapatici Tecnologia:")
    print(" - Pode escanear o QR Code pelo app do TikTok no celular")
    print(" - Ou entrar com e-mail/usuário e senha")
    print("\nAssim que você autenticar, o script detectará automaticamente")
    print("a chave de sessão e salvará tudo com segurança!")
    print("=" * 60 + "\n", flush=True)

    with sync_playwright() as p:
        browser = get_browser_instance(p, headless=False)
        context = browser.new_context(
            no_viewport=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        target_url = "https://www.tiktok.com/login?redirect_url=https%3A%2F%2Fwww.tiktok.com%2Fcreator-center%2Fupload%3Ffrom%3Dcreator_center"
        print("[TIKTOK] 🌐 Carregando página de autenticação...")
        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        print("[TIKTOK] ⏳ Aguardando você realizar o login no navegador aberto...")
        start_time = time.time()
        logged_in = False

        # Aguarda até o cookie de sessão 'sessionid' ser criado após o login do usuário
        while time.time() - start_time < 300: # 5 minutos
            try:
                cookies = context.cookies()
                has_session = any(c.get("name") in ["sessionid", "sessionid_ss", "sid_tt"] and c.get("value") for c in cookies)
                if has_session:
                    print("\n[TIKTOK] 🔑 Cookie de sessão 'sessionid' detectado!")
                    page.wait_for_timeout(3000)
                    logged_in = True
                    break
            except Exception:
                break
            time.sleep(2)

        if not logged_in:
            print("\n[TIKTOK] ⚠️ Tempo limite excedido ou login não concluído.")
            browser.close()
            return False

        # Salva o estado da sessão (cookies e storage)
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        context.storage_state(path=SESSION_FILE)
        print(f"[TIKTOK] ✅ Sessão salva com sucesso em: {SESSION_FILE}")
        browser.close()
        return True

def dismiss_modals(page):
    """Fecha janelas pop-up, termos de verificação de direitos autorais e sobreposições do TikTok."""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(800)
        # Botões de confirmação comuns nas modais do TikTok Creator Center
        modal_btns = page.locator("button:has-text('Entendi'), button:has-text('Got it'), button:has-text('OK'), button:has-text('Continuar'), button:has-text('Fechar'), button.TUXButton--primary")
        count = modal_btns.count()
        for i in range(count):
            try:
                btn = modal_btns.nth(i)
                if btn.is_visible():
                    btn.click(timeout=2000, force=True)
                    page.wait_for_timeout(500)
            except Exception:
                pass
    except Exception:
        pass

def upload_video(project_id: str):
    """Envia o output_shorts.mp4 de um projeto para o TikTok com legenda otimizada."""
    project_dir = os.path.join(PROJECT_DIR, "projects", project_id)
    video_path = os.path.join(project_dir, "output_shorts.mp4")
    script_path = os.path.join(project_dir, "script.json")

    if not os.path.exists(video_path):
        print(f"[TIKTOK] ❌ Arquivo output_shorts.mp4 não encontrado em: {video_path}")
        return False

    if not os.path.exists(SESSION_FILE):
        print("\n" + "=" * 60)
        print("[TIKTOK] ⚠️ Sessão não encontrada!")
        print("Para configurar a publicação automática no TikTok, execute:")
        print("python pipeline/publishing/tiktok_uploader.py --setup")
        print("=" * 60 + "\n")
        return False

    title = "Mistério do Universo"
    seo_desc = ""
    tags = ["scapaticitecnologia", "astronomia", "ciencia", "curiosidades", "fatos", "universo", "fy", "foryou"]
    if os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", title)
                seo_desc = data.get("seo", {}).get("description", "")
                custom_tags = data.get("seo", {}).get("tags", [])
                for ct in custom_tags:
                    clean_tag = ct.replace(" ", "").replace("-", "").lower()
                    if clean_tag and clean_tag not in tags:
                        tags.insert(0, clean_tag)
        except Exception:
            pass

    # Verifica se há link do vídeo longo oficial do YouTube
    info_16x9_path = os.path.join(project_dir, "youtube_16x9_info.json")
    yt_url = None
    if os.path.exists(info_16x9_path):
        try:
            with open(info_16x9_path, "r", encoding="utf-8") as f:
                yt_url = json.load(f).get("video_url")
        except Exception:
            pass

    caption_tags = " ".join([f"#{t}" for t in tags[:7]])
    if yt_url:
        caption = (
            f"{title[:85]} ⚛️\n\n"
            f"💬 O que você acha disso? Comenta aqui!\n"
            f"👉 Documentário completo no YouTube: {yt_url}\n"
            f"🔔 Siga @scapatici.tecnologia\n\n{caption_tags}"
        )
    elif seo_desc:
        caption = (
            f"{title[:90]} ⚛️\n\n{seo_desc[:180]}\n\n"
            "💬 Qual sua teoria? Siga @scapatici.tecnologia e inscreva-se no YouTube!\n"
            f"{caption_tags}"
        )
    else:
        caption = (
            f"{title[:95]} ⚛️\n\n"
            "💬 Comente sua opinião e siga @scapatici.tecnologia para ciência profunda todos os dias!\n"
            f"{caption_tags}"
        )

    print("\n" + "=" * 60)
    print(f"🚀 INICIANDO UPLOAD NO TIKTOK: {project_id}")
    print("=" * 60)
    print(f"📦 Arquivo: {video_path} ({round(os.path.getsize(video_path) / (1024*1024), 1)} MB)")
    print(f"📝 Legenda:\n{caption}")
    print("=" * 60 + "\n", flush=True)

    for attempt in range(1, 3):
        with sync_playwright() as p:
            browser = get_browser_instance(p, headless=False)
            context = browser.new_context(
                storage_state=SESSION_FILE,
                viewport={"width": 1280, "height": 850},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
            )
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

            try:
                print(f"[TIKTOK] 🌐 Acessando a página de upload do TikTok Creator Center (tentativa {attempt}/2)...")
                page.goto("https://www.tiktok.com/creator-center/upload?from=creator_center", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)

                # Verifica se foi redirecionado para login
                if "login" in page.url.lower():
                    print("[TIKTOK] ⚠️ Sessão expirada! Execute novamente: python pipeline/publishing/tiktok_uploader.py --setup")
                    browser.close()
                    return False

                print("[TIKTOK] ⏳ Localizando campo de upload...")
                file_input = page.locator("input[type='file']").first
                file_input.wait_for(state="attached", timeout=30000)

                print(f"[TIKTOK] 📤 Enviando arquivo de vídeo: {os.path.basename(video_path)}...")
                file_input.set_input_files(os.path.abspath(video_path))

                # Aguarda upload e processamento inicial
                print("[TIKTOK] ⏳ Aguardando carregamento e processamento do vídeo pelo TikTok...")
                page.wait_for_timeout(15000)

                # Fecha eventuais modais (aviso de verificação automática de direitos autorais)
                dismiss_modals(page)

                # Preencher a legenda / título
                print("[TIKTOK] ✍️ Inserindo legenda e hashtags...")
                try:
                    editor = page.locator("div.public-DraftEditor-content, div[contenteditable='true'], div[data-placeholder], textarea").first
                    editor.wait_for(state="attached", timeout=15000)
                    dismiss_modals(page)
                    editor.click(force=True)
                    page.keyboard.press("Control+A")
                    page.keyboard.press("Backspace")
                    page.keyboard.type(caption, delay=15)
                    print("[TIKTOK] ✅ Legenda preenchida com sucesso!")
                except Exception as ee:
                    print(f"[TIKTOK] ⚠️ Aviso ao preencher legenda: {ee}")

                page.wait_for_timeout(6000)
                dismiss_modals(page)

                # Localizar botão de Publicar
                print("[TIKTOK] 🚀 Localizando botão de Publicar...")
                post_selectors = [
                    "button[data-e2e='post_video_button']",
                    "button:has-text('Publicar')",
                    "button:has-text('Post')",
                    "button:has-text('Carregar')",
                    "button.btn-post"
                ]

                post_button = None
                for sel in post_selectors:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        post_button = btn
                        break

                if post_button:
                    print("[TIKTOK] ⏳ Aguardando liberação do botão Publicar...")
                    page.wait_for_timeout(4000)
                    dismiss_modals(page)
                    
                    print("[TIKTOK] 🚀 Clicando no botão Publicar...")
                    post_button.click(force=True)
                    page.wait_for_timeout(3000)

                    # Trata eventuais modais sequenciais de confirmação do TikTok (ex: "Ativar" -> "Publicar agora")
                    for m_round in range(5):
                        ativar_btn = page.locator("button:has-text('Ativar'), button:has-text('Permitir')").first
                        if ativar_btn.count() > 0 and ativar_btn.is_visible():
                            print("[TIKTOK] 🛡️ Modal de verificação detectada. Clicando em 'Ativar'...")
                            ativar_btn.click(force=True)
                            page.wait_for_timeout(3000)

                        pub_agora = page.locator("button:has-text('Publicar agora'), button:has-text('Post now')").first
                        if pub_agora.count() > 0 and pub_agora.is_visible():
                            print("[TIKTOK] 🚀 Modal de confirmação final detectada. Clicando em 'Publicar agora'...")
                            pub_agora.click(force=True)
                            page.wait_for_timeout(4000)
                            break

                        try:
                            if post_button.is_visible() and not page.locator(".TUXModal-overlay").is_visible():
                                post_button.click(force=True)
                        except Exception:
                            pass
                        page.wait_for_timeout(2000)

                    print("[TIKTOK] ⏳ Aguardando tela de sucesso / pós-publicação...")
                    success = False
                    for i in range(25): # até 50 segundos
                        page.wait_for_timeout(2000)
                        try:
                            page_text = page.inner_text("body").lower()
                            curr_url = page.url.lower()
                            if (
                                "seu vídeo foi publicado" in page_text
                                or "gerenciar seus vídeos" in page_text
                                or "carregar outro vídeo" in page_text
                                or "post another video" in page_text
                                or "publicações" in page_text
                                or "conteúdo (criado em)" in page_text
                                or "manage" in curr_url
                                or "content" in curr_url
                            ):
                                print("[TIKTOK] 🎉 SUCESSO CONFIRMADO: O vídeo foi oficialmente publicado no TikTok!")
                                success = True
                                break
                        except Exception:
                            pass

                    try:
                        page.screenshot(path=os.path.join(SCRIPT_DIR, "tiktok_upload_result.png"))
                    except Exception:
                        pass

                    if success:
                        try:
                            with open(os.path.join(project_dir, "tiktok_info.json"), "w", encoding="utf-8") as tf:
                                json.dump({"published": True, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}, tf, indent=2)
                        except Exception:
                            pass
                    else:
                        print("[TIKTOK] ⚠️ Confirmação pós-upload não detectada, mas botão foi acionado. Verifique o resultado do screenshot.")
                else:
                    print("[TIKTOK] ⚠️ Botão de publicar não encontrado automaticamente.")
                    success = False

                browser.close()
                if success:
                    return True
                if attempt < 2:
                    print("[TIKTOK] 🔄 Repetindo tentativa de upload em 8s...")
                    time.sleep(8)
                else:
                    return False

            except Exception as e:
                print(f"[TIKTOK] ⚠️ Erro na tentativa {attempt}/2 durante upload: {e}")
                try:
                    browser.close()
                except Exception:
                    pass
                if attempt < 2:
                    time.sleep(8)
                else:
                    return False

def main():
    parser = argparse.ArgumentParser(description="Simple-Tube TikTok Uploader")
    parser.add_argument("--project", type=str, default="video-014-quasi-stars", help="ID do projeto")
    parser.add_argument("--setup", action="store_true", help="Abre o navegador para autenticação e salva sessão")
    parser.add_argument("--sessionid", type=str, help="Configura diretamente via valor do cookie sessionid copiado do navegador")

    args = parser.parse_args()

    if args.sessionid:
        if set_session_cookie(args.sessionid):
            ok = upload_video(args.project)
    if not ok:
        sys.exit(1)
        return

    if args.setup:
        setup_session()
        return

    ok = upload_video(args.project)
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
