"""
Simple-Tube Instagram Uploader
Faz upload automático de Reels no Instagram a partir do output_shorts.mp4
usando a biblioteca instagrapi com persistência de sessão.
"""

import os
import sys
import json
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    TwoFactorRequired,
    ChallengeRequired,
    BadPassword,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "instagram_credentials.json")
SESSION_FILE = os.path.join(SCRIPT_DIR, "instagram_session.json")

def load_credentials():
    """Carrega usuário, senha ou sessionid do arquivo instagram_credentials.json."""
    if not os.path.exists(CREDENTIALS_FILE):
        return None, None, None
    try:
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return (
                data.get("username", "").strip(),
                data.get("password", "").strip(),
                data.get("sessionid", "").strip()
            )
    except Exception as e:
        print(f"[INSTA] ⚠️ Erro ao ler credenciais: {e}", flush=True)
        return None, None, None

def get_authenticated_client(username=None, password=None, session_id=None, verification_code=None):
    """Inicializa e autentica o cliente do Instagram com persistência de sessão."""
    cl = Client()
    cl.delay_range = [2, 5]

    file_user, file_pass, file_sessionid = load_credentials()
    user = username or file_user or os.environ.get("INSTAGRAM_USER")
    pwd = password or file_pass or os.environ.get("INSTAGRAM_PASS")
    sess_id = session_id or file_sessionid or os.environ.get("INSTAGRAM_SESSIONID")

    code_2fa_file = os.path.join(SCRIPT_DIR, "2fa_code.txt")
    v_code = verification_code
    if not v_code and os.path.exists(code_2fa_file):
        try:
            with open(code_2fa_file, "r", encoding="utf-8") as f:
                v_code = f.read().strip()
        except Exception:
            pass

    # 1. Tenta restaurar sessão existente primeiro
    if os.path.exists(SESSION_FILE):
        try:
            print("[INSTA] 🔄 Restaurando sessão salva em cache...", flush=True)
            cl.load_settings(SESSION_FILE)
            if user and pwd:
                cl.login(user, pwd)
            print("[INSTA] ✅ Sessão restaurada com sucesso!", flush=True)
            return cl
        except Exception as e:
            print(f"[INSTA] ⚠️ Falha ao restaurar sessão ({e}). Tentando nova conexão...", flush=True)
            cl.set_settings({})

    # 2. Login via Session ID do navegador (o método mais estável e seguro sem 2FA)
    if sess_id:
        try:
            print("[INSTA] 🔑 Conectando diretamente via sessionid do navegador...", flush=True)
            cl.login_by_sessionid(sess_id)
            cl.dump_settings(SESSION_FILE)
            print(f"[INSTA] ✅ Login via sessionid concluído com sucesso! Sessão salva em: {SESSION_FILE}", flush=True)
            return cl
        except Exception as e:
            print(f"[INSTA] ⚠️ Falha no login por sessionid: {e}", flush=True)

    if not user or not pwd:
        print("\n" + "=" * 60, flush=True)
        print("📸 CONFIGURAÇÃO DO INSTAGRAM NECESSÁRIA", flush=True)
        print("Para postar Reels automaticamente, configure suas credenciais em:", flush=True)
        print(f"👉 {CREDENTIALS_FILE}", flush=True)
        print("Opção 1 (Recomendada): Copie o sessionid do cookie do navegador", flush=True)
        print('{\n  "sessionid": "seu_cookie_sessionid"\n}', flush=True)
        print("Opção 2: Usuário e Senha", flush=True)
        print('{\n  "username": "seu_usuario",\n  "password": "sua_senha"\n}', flush=True)
        print("=" * 60 + "\n", flush=True)
        return None

    # 3. Novo login via Usuário e Senha
    try:
        print(f"[INSTA] 🔑 Realizando login como @{user}...", flush=True)
        if v_code:
            try:
                cl.login(user, pwd, verification_code=v_code)
            except Exception:
                cl.login_legacy(user, pwd, verification_code=v_code)
        else:
            cl.login(user, pwd)
        cl.dump_settings(SESSION_FILE)
        print(f"[INSTA] ✅ Login bem-sucedido! Sessão salva em: {SESSION_FILE}", flush=True)
        if os.path.exists(code_2fa_file):
            try: os.remove(code_2fa_file)
            except Exception: pass
        return cl
    except TwoFactorRequired:
        print("\n[INSTA] 🔒 Autenticação de Dois Fatores (2FA) necessária!", flush=True)
        code = v_code or input("[INSTA] Digite o novo código 2FA recebido no app/SMS: ")
        try:
            cl.login(user, pwd, verification_code=code.strip())
        except Exception:
            cl.login_legacy(user, pwd, verification_code=code.strip())
        cl.dump_settings(SESSION_FILE)
        print(f"[INSTA] ✅ Login 2FA concluído com sucesso! Sessão salva em: {SESSION_FILE}", flush=True)
        if os.path.exists(code_2fa_file):
            try: os.remove(code_2fa_file)
            except Exception: pass
        return cl
    except ChallengeRequired:
        print("\n[INSTA] ⚠️ Desafio de verificação do Instagram solicitado. Acesse o aplicativo do Instagram no celular para autorizar o acesso.", flush=True)
        return None
    except BadPassword:
        print("\n[INSTA] ❌ Senha incorreta. Verifique o arquivo instagram_credentials.json.", flush=True)
        return None
    except Exception as e:
        print(f"\n[INSTA] ❌ Erro ao conectar com o Instagram: {e}", flush=True)
        return None

def upload_reel(project_id, username=None, password=None, verification_code=None):
    """Envia o arquivo output_shorts.mp4 como Instagram Reel."""
    project_dir = os.path.join("projects", project_id)
    script_path = os.path.join(project_dir, "script.json")
    video_path = os.path.join(project_dir, "output_shorts.mp4")
    thumbnail_path = os.path.join(project_dir, "thumbnail.jpg")

    if not os.path.exists(video_path):
        print(f"[INSTA] ❌ Arquivo vertical output_shorts.mp4 não encontrado em: {video_path}", flush=True)
        print("Renderize a versão vertical primeiro com: node pipeline/orchestrator.js render <id> shorts", flush=True)
        return False

    title = f"Vídeo {project_id}"
    topic_desc = ""
    tags = []
    if os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", title)
                raw_desc = data.get("seo", {}).get("description", "")
                topic_desc = raw_desc.split("\n")[0].strip() if raw_desc else data.get("topic", "")
                tags = data.get("seo", {}).get("tags", [])
        except Exception:
            pass

    if not topic_desc:
        topic_desc = "Uma investigação científica reveladora sobre as maiores fronteiras do cosmos e da tecnologia."

    # Monta legenda otimizada para retenção, comentários e ganho de seguidores
    hashtags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags[:8] if t])
    caption = (
        f"⚛️ {title}\n\n"
        f"{topic_desc[:260]}\n\n"
        "💬 Qual é a sua teoria sobre esse mistério? Deixe nos comentários!\n"
        "🔔 Siga @scapatici.tecnologia para 3 episódios diários de ciência profunda.\n"
        "👇 Link do documentário completo no YouTube fixado no primeiro comentário!\n\n"
        ".\n.\n"
        f"{hashtags_str} #scapaticitecnologia #ciencia #astronomia #fisica #universo #curiosidades #reels"
    )

    client = get_authenticated_client(username=username, password=password, verification_code=verification_code)
    if not client:
        return False

    print("\n" + "=" * 60, flush=True)
    print(f"🚀 INICIANDO UPLOAD NO INSTAGRAM REELS: {project_id}", flush=True)
    print("=" * 60, flush=True)
    print(f"📦 Arquivo: {video_path} ({round(os.path.getsize(video_path) / (1024*1024), 1)} MB)", flush=True)
    print(f"📝 Legenda:\n{caption[:180]}...", flush=True)
    print("=" * 60 + "\n", flush=True)

    import time
    thumb = thumbnail_path if os.path.exists(thumbnail_path) else None
    last_err = None
    for attempt in range(1, 3):
        try:
            print(f"[INSTA] 📤 Enviando Reel para os servidores do Instagram (tentativa {attempt}/2)...", flush=True)
            media = client.clip_upload(
                path=video_path,
                caption=caption,
                thumbnail=thumb
            )
            reel_url = f"https://www.instagram.com/reel/{media.code}/"
            print(f"\n[INSTA] 🎉 Reel publicado com sucesso!", flush=True)
            print(f"🔗 ID da Publicação: {media.id}", flush=True)
            print(f"🌐 Link Direto: {reel_url}", flush=True)

            # Salva confirmação local para evitar duplicidade em reexecuções
            try:
                with open(os.path.join(project_dir, "instagram_info.json"), "w", encoding="utf-8") as inf:
                    json.dump({"media_id": str(media.id), "reel_url": reel_url}, inf, indent=2)
            except Exception:
                pass

            # Busca link do vídeo completo no YouTube
            info_16x9_path = os.path.join(project_dir, "youtube_16x9_info.json")
            full_video_url = None
            if os.path.exists(info_16x9_path):
                try:
                    with open(info_16x9_path, "r", encoding="utf-8") as f:
                        full_video_url = json.load(f).get("video_url")
                except Exception:
                    pass

            # Publica o primeiro comentário com o link do documentário completo
            if full_video_url:
                comment_text = (
                    f"🛸 Assista ao documentário completo e detalhado no YouTube:\n"
                    f"👉 {full_video_url}\n\n"
                    f"💬 E aí, qual foi a parte mais chocante? Siga @scapatici.tecnologia!"
                )
            else:
                comment_text = (
                    "🛸 Assista à investigação completa no nosso canal oficial do YouTube: Scapatici Tecnologia!\n"
                    "👉 Link no topo da nossa Bio! Siga @scapatici.tecnologia!"
                )

            try:
                print(f"[INSTA] 💬 Publicando primeiro comentário com o link do vídeo completo...", flush=True)
                c = client.media_comment(media.id, comment_text)
                c_pk = getattr(c, "pk", getattr(c, "id", "ok"))
                print(f"[INSTA] ✅ Primeiro comentário com link publicado com sucesso no Reels! (ID: {c_pk})", flush=True)
            except Exception as ce:
                print(f"[INSTA] ⚠️ Não foi possível postar o comentário automático no Reels: {ce}", flush=True)

            print("=" * 60 + "\n", flush=True)
            return True
        except Exception as e:
            last_err = e
            print(f"\n[INSTA] ⚠️ Erro na tentativa {attempt}/2 ao publicar Reel: {e}", flush=True)
            if attempt < 2:
                time.sleep(10)

    print(f"\n[INSTA] ❌ Falha definitiva ao publicar Reel: {last_err}", flush=True)
    return False

def main():
    parser = argparse.ArgumentParser(description="Simple-Tube Instagram Reels Uploader")
    parser.add_argument("--project", type=str, default="video-006-quantum-entanglement", help="ID do projeto")
    parser.add_argument("--username", type=str, default=None, help="Usuário do Instagram")
    parser.add_argument("--password", type=str, default=None, help="Senha do Instagram")
    parser.add_argument("--code", type=str, default=None, help="Código 2FA de verificação")

    args = parser.parse_args()
    ok = upload_reel(args.project, username=args.username, password=args.password, verification_code=args.code)
    if not ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
