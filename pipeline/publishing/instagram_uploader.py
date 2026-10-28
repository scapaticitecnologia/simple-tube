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
    tags = []
    if os.path.exists(script_path):
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", title)
                tags = data.get("seo", {}).get("tags", [])
        except Exception:
            pass

    # Monta a legenda do Reel
    hashtags_str = " ".join([f"#{t.replace(' ', '')}" for t in tags[:10] if t])
    caption = (
        f"⚛️ {title}\n\n"
        "Se o universo não é o que parece no nível fundamental, o que isso significa para a nossa realidade?\n\n"
        "👇 Assista ao documentário completo em alta definição no nosso canal do YouTube: Scapatici Tecnologia (Link na Bio)!\n\n"
        ".\n.\n"
        f"{hashtags_str} #scapaticitecnologia #ciencia #fisicaquantica #cosmos #universo #reels #curiosidades #fatos"
    )

    client = get_authenticated_client(username=username, password=password, verification_code=verification_code)
    if not client:
        return False

    print("\n" + "=" * 60, flush=True)
    print(f"🚀 INICIANDO UPLOAD NO INSTAGRAM REELS: {project_id}", flush=True)
    print("=" * 60, flush=True)
    print(f"📦 Arquivo: {video_path} ({round(os.path.getsize(video_path) / (1024*1024), 1)} MB)", flush=True)
    print(f"📝 Legenda:\n{caption[:140]}...", flush=True)
    print("=" * 60 + "\n", flush=True)

    try:
        thumb = thumbnail_path if os.path.exists(thumbnail_path) else None
        print("[INSTA] 📤 Enviando Reel para os servidores do Instagram...", flush=True)
        media = client.clip_upload(
            path=video_path,
            caption=caption,
            thumbnail=thumb
        )
        print(f"\n[INSTA] 🎉 Reel publicado com sucesso!", flush=True)
        print(f"🔗 ID da Publicação: {media.id}", flush=True)
        print(f"🌐 Link Direto: https://www.instagram.com/reel/{media.code}/", flush=True)

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
                f"🛸 Assista à investigação completa no YouTube:\n"
                f"👉 {full_video_url}\n\n"
                f"Inscreva-se no canal Scapatici Tecnologia!"
            )
        else:
            comment_text = (
                "🛸 Assista à investigação completa no nosso canal oficial do YouTube: Scapatici Tecnologia!\n"
                "👉 Link no topo da nossa Bio!"
            )

        try:
            print(f"[INSTA] 💬 Publicando primeiro comentário com o link do vídeo completo...", flush=True)
            client.media_comment(media.id, comment_text)
            print(f"[INSTA] ✅ Primeiro comentário com link publicado com sucesso no Reels!", flush=True)
        except Exception as ce:
            print(f"[INSTA] ⚠️ Não foi possível postar o comentário automático no Reels: {ce}", flush=True)

        print("=" * 60 + "\n", flush=True)
        return True
    except Exception as e:
        print(f"\n[INSTA] ❌ Erro ao publicar Reel: {e}", flush=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="Simple-Tube Instagram Reels Uploader")
    parser.add_argument("--project", type=str, default="video-006-quantum-entanglement", help="ID do projeto")
    parser.add_argument("--username", type=str, default=None, help="Usuário do Instagram")
    parser.add_argument("--password", type=str, default=None, help="Senha do Instagram")
    parser.add_argument("--code", type=str, default=None, help="Código 2FA de verificação")

    args = parser.parse_args()
    upload_reel(args.project, username=args.username, password=args.password, verification_code=args.code)

if __name__ == "__main__":
    main()
