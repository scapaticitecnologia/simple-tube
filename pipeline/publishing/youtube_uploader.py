"""
Simple-Tube YouTube Uploader
Faz upload automático de vídeos, miniaturas e metadados completos
usando a API oficial do YouTube v3 (OAuth 2.0).
"""

import os
import sys
import json
import time
import argparse
import http.client
import httplib2
import random

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Escopos necessários para upload e gerenciamento de vídeos e thumbnails
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error, IOError, http.client.NotConnected,
    http.client.IncompleteRead, http.client.ImproperConnectionState,
    http.client.CannotSendRequest, http.client.CannotSendHeader,
    http.client.ResponseNotReady, http.client.BadStatusLine
)

def get_authenticated_service():
    """Obtém ou renova as credenciais OAuth 2.0 e inicializa a API do YouTube."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"[AUTH] Token existente inválido ({e}), solicitando nova autorização...")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[AUTH] 🔄 Renovando token de acesso expirado...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"[AUTH] Falha ao renovar ({e}), iniciando fluxo web...")
                creds = None

        if not creds:
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(f"[ERRO] client_secret.json não encontrado em: {CLIENT_SECRET_FILE}")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            # Obter a URL de autorização antecipadamente para salvar e exibir ao usuário
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            auth_url_file = os.path.join(SCRIPT_DIR, "auth_url.txt")
            with open(auth_url_file, "w", encoding="utf-8") as f:
                f.write(auth_url)

            print("\n" + "=" * 60)
            print("🔑 AUTORIZAÇÃO DO YOUTUBE (OAUTH 2.0)")
            print("Abra o seguinte link no seu navegador para autorizar:")
            print(f"\n{auth_url}\n")
            print("=" * 60 + "\n", flush=True)

            creds = flow.run_local_server(port=8088, open_browser=False)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())
        print(f"[AUTH] ✅ Token salvo com sucesso em: {TOKEN_FILE}", flush=True)
        if os.path.exists(os.path.join(SCRIPT_DIR, "auth_url.txt")):
            try:
                os.remove(os.path.join(SCRIPT_DIR, "auth_url.txt"))
            except Exception:
                pass

    return build("youtube", "v3", credentials=creds)

def upload_thumbnail(youtube, video_id, thumbnail_path):
    """Envia a thumbnail personalizada para o vídeo no YouTube."""
    if not os.path.exists(thumbnail_path):
        print(f"[THUMB] ⚠️ Thumbnail não encontrada em: {thumbnail_path}")
        return False

    print(f"[THUMB] 🖼️ Enviando miniatura oficial: {thumbnail_path}...")
    try:
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg", resumable=True)
        )
        request.execute()
        print(f"[THUMB] ✅ Miniatura configurada com sucesso!")
        return True
    except HttpError as e:
        print(f"[THUMB] ❌ Erro ao enviar thumbnail: {e}")
        return False

def upload_video(project_id, privacy_status="private", video_format="16x9"):
    """Realiza o upload completo do vídeo com metadados e thumbnail (16x9 ou shorts)."""
    project_dir = os.path.join("projects", project_id)
    script_path = os.path.join(project_dir, "script.json")
    video_filename = "output_shorts.mp4" if video_format == "shorts" else "output_16x9.mp4"
    video_path = os.path.join(project_dir, video_filename)
    thumbnail_path = os.path.join(project_dir, "thumbnail.jpg")

    if not os.path.exists(script_path):
        print(f"[ERRO] Arquivo script.json não encontrado em: {script_path}")
        return None

    if not os.path.exists(video_path):
        print(f"[ERRO] Vídeo {video_filename} não encontrado em: {video_path}")
        print(f"Certifique-se de renderizar o vídeo ({video_format}) antes de publicar!")
        return None

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seo = data.get("seo", {})
    raw_title = seo.get("title_options", [data.get("title", f"Vídeo {project_id}")])[0]

    info_16x9_path = os.path.join(project_dir, "youtube_16x9_info.json")
    full_video_url = None
    if os.path.exists(info_16x9_path):
        try:
            with open(info_16x9_path, "r", encoding="utf-8") as f:
                full_video_url = json.load(f).get("video_url")
        except Exception:
            pass

    if video_format == "shorts":
        # No Shorts, garantir que o título tenha a hashtag #Shorts e respeite o limite de 100 caracteres
        suffix = " #Shorts"
        max_base_len = 100 - len(suffix)
        base_title = raw_title[:max_base_len].rstrip()
        title = f"{base_title}{suffix}"
        
        link_header = f"🚀 ASSISTA AO VÍDEO COMPLETO: {full_video_url}\n\n" if full_video_url else ""
        description = (
            f"{link_header}"
            "⚡ Assista ao documentário completo no canal Scapatici Tecnologia!\n"
            "Inscreva-se para desvendar os maiores enigmas da astrofísica e do universo.\n\n"
            + seo.get("description", "")
            + "\n\n#Shorts #ScapaticiTecnologia #Astrofisica #Ciencia"
        )
        tags = list(set(seo.get("tags", []) + ["shorts", "youtube shorts", "curiosidades", "fatos rapidos", "ciencia"]))
    else:
        title = raw_title
        description = seo.get("description", "")
        tags = seo.get("tags", ["scapatici tecnologia", "ciencia", "tecnologia"])

    print("\n" + "=" * 60)
    print(f"🚀 INICIANDO UPLOAD AUTOMÁTICO ({video_format.upper()}): {project_id}")
    print("=" * 60)
    print(f"📌 Título: {title}")
    print(f"🔒 Privacidade: {privacy_status.upper()}")
    print(f"📦 Arquivo: {video_path} ({round(os.path.getsize(video_path) / (1024*1024), 1)} MB)")
    print("=" * 60 + "\n")

    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "28",  # 28 = Ciência e Tecnologia
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR"
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    # Upload resumable em blocos de 8MB
    media = MediaFileUpload(video_path, chunksize=8*1024*1024, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    retry_count = 0
    max_retries = 10

    print("[UPLOAD] 📤 Transmitindo arquivo para os servidores do YouTube...")
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                percent = int(status.progress() * 100)
                sys.stdout.write(f"\r[UPLOAD] ⏳ Progresso: {percent}% enviado...")
                sys.stdout.flush()
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                retry_count += 1
                if retry_count > max_retries:
                    print(f"\n[ERRO] Limite de tentativas excedido: {e}")
                    raise
                sleep_time = (2 ** retry_count) + random.random()
                print(f"\n[RETRY] Erro temporário {e.resp.status}. Aguardando {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            else:
                print(f"\n[ERRO] Falha fatal na API: {e}")
                raise
        except RETRIABLE_EXCEPTIONS as e:
            retry_count += 1
            if retry_count > max_retries:
                print(f"\n[ERRO] Limite de tentativas de conexão excedido: {e}")
                raise
            sleep_time = (2 ** retry_count) + random.random()
            print(f"\n[RETRY] Falha de conexão ({e}). Reconectando em {sleep_time:.1f}s...")
            time.sleep(sleep_time)

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"

    # Salva informações do vídeo publicado no projeto
    info_file = os.path.join(project_dir, f"youtube_{video_format}_info.json")
    try:
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump({
                "video_id": video_id,
                "video_url": video_url,
                "format": video_format,
                "privacy": privacy_status
            }, f, indent=2)
    except Exception as ie:
        print(f"[AVISO] Não foi possível salvar {info_file}: {ie}")

    print(f"\n\n[SUCESSO] 🎉 Vídeo enviado com sucesso!")
    print(f"🔗 ID do Vídeo: {video_id}")
    print(f"🌐 Link Direto: {video_url}")

    # Envia a thumbnail
    if os.path.exists(thumbnail_path):
        upload_thumbnail(youtube, video_id, thumbnail_path)

    # Se for Shorts e tiver link do vídeo longo, posta o primeiro comentário fixado
    if video_format == "shorts" and full_video_url:
        try:
            print("[YOUTUBE] 💬 Postando primeiro comentário no Shorts com o link do documentário...")
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": f"🚀 Assista ao documentário completo em alta definição aqui:\n👉 {full_video_url}\n\nInscreva-se no canal Scapatici Tecnologia!"
                            }
                        }
                    }
                }
            ).execute()
            print("[YOUTUBE] ✅ Primeiro comentário com link publicado no Shorts com sucesso!")
        except Exception as ce:
            print(f"[YOUTUBE] ⚠️ Não foi possível postar o comentário automático no Shorts: {ce}")

    print("\n" + "=" * 60)
    print("✅ PROCESSO DE PUBLICAÇÃO CONCLUÍDO!")
    print(f"Acesse o YouTube Studio para revisar ou gerenciar: https://studio.youtube.com/video/{video_id}/edit")
    print("=" * 60 + "\n")

    return video_id

def main():
    parser = argparse.ArgumentParser(description="Simple-Tube YouTube Uploader")
    parser.add_argument("--project", type=str, default="video-004-dark-universe", help="ID do projeto")
    parser.add_argument("--privacy", type=str, choices=["private", "unlisted", "public"], default="private", help="Status de privacidade inicial")
    parser.add_argument("--format", type=str, choices=["16x9", "shorts"], default="16x9", help="Formato do vídeo (16x9 ou shorts)")
    parser.add_argument("--auth-only", action="store_true", help="Apenas autentica e salva o token")

    args = parser.parse_args()

    if args.auth_only:
        get_authenticated_service()
        print("[AUTH] Autenticação concluída com sucesso.")
        return

    upload_video(args.project, privacy_status=args.privacy, video_format=args.format)

if __name__ == "__main__":
    main()
