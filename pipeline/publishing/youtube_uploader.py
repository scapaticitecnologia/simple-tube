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
import http.server
import urllib.parse
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

# Escopos necessários para upload, gerenciamento de vídeos, thumbnails e comentários
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
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

def _write_auth_alert(reason: str):
    alert_file = os.path.join(os.path.dirname(SCRIPT_DIR), "health_alert.json")
    try:
        with open(alert_file, "w", encoding="utf-8") as f:
            json.dump({
                "service": "youtube_oauth",
                "status": "ACTION_REQUIRED",
                "reason": reason,
                "fix_command": "python pipeline/publishing/youtube_uploader.py --auth-only",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }, f, indent=2)
    except Exception:
        pass


def get_authenticated_service(force_reauth=False, non_interactive=False):
    """Obtém ou renova as credenciais OAuth 2.0 e inicializa a API do YouTube sem travar processos automáticos."""
    is_unattended = non_interactive or (os.environ.get("AUTOPILOT_UNATTENDED") == "1")
    creds = None
    if os.path.exists(TOKEN_FILE) and not force_reauth:
        try:
            # Usa os escopos já autorizados no token.json para não quebrar execuções automáticas
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
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

            if is_unattended:
                _write_auth_alert("Token OAuth do YouTube expirou ou foi revogado em modo automático.")
                print("[AUTH] ❌ Token expirado em modo não-interativo (AUTOPILOT_UNATTENDED=1). Abortando sem travar outras redes.", flush=True)
                print("👉 Execute manualmente: python pipeline/publishing/youtube_uploader.py --auth-only", flush=True)
                sys.exit(2)

            redirect_uri = "http://localhost:8088/"
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES,
                redirect_uri=redirect_uri
            )
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

            auth_code = None

            class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    nonlocal auth_code
                    parsed = urllib.parse.urlparse(self.path)
                    params = urllib.parse.parse_qs(parsed.query)
                    if 'code' in params:
                        auth_code = params['code'][0]
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html; charset=utf-8')
                        self.end_headers()
                        html = """
                        <html><body style="font-family:Segoe UI,sans-serif;text-align:center;padding:60px;background:#0B0F19;color:#00F2FE;">
                        <h1 style="font-size:32px;margin-bottom:12px;">✅ Autenticação do YouTube Concluída!</h1>
                        <p style="color:#F3F4F6;font-size:18px;">O Simple-Tube já recebeu as credenciais com sucesso.</p>
                        <p style="color:#9CA3AF;font-size:14px;margin-top:24px;">Você já pode fechar esta aba com segurança.</p>
                        </body></html>
                        """
                        self.wfile.write(html.encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b"Erro: Codigo de autorizacao ausente.")

                def log_message(self, format, *args):
                    return

            server = http.server.HTTPServer(('localhost', 8088), OAuthCallbackHandler)
            server.timeout = 180

            print("\n" + "=" * 60)
            print("🔑 AUTORIZAÇÃO DO YOUTUBE (OAUTH 2.0) — TIMEOUT 180s")
            print("Abra o seguinte link no seu navegador para autorizar (ou aguarde a abertura automática):")
            print(f"\n{auth_url}\n")
            print("=" * 60 + "\n", flush=True)

            try:
                import webbrowser
                webbrowser.open(auth_url)
            except Exception:
                pass

            deadline = time.time() + 180
            while auth_code is None and time.time() < deadline:
                server.handle_request()

            server.server_close()

            if not auth_code:
                _write_auth_alert("Tempo limite de 180s excedido aguardando autorização OAuth.")
                print("[AUTH] ❌ Tempo limite de autorização excedido.", flush=True)
                sys.exit(2)

            print("[AUTH] 🔄 Trocando código de autorização por novo token...")
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

        with open(TOKEN_FILE, "w", encoding="utf-8") as token_out:
            token_out.write(creds.to_json())
        print(f"[AUTH] ✅ Token salvo com sucesso em: {TOKEN_FILE}", flush=True)

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

def _build_chapters_text(project_dir: str, data: dict) -> str:
    """Gera capítulos automáticos (timestamps SEO) para a descrição do YouTube 16:9."""
    sub_path = os.path.join(project_dir, "subtitles.json")
    scenes = data.get("scenes", [])
    if not scenes or not os.path.exists(sub_path):
        return ""
    try:
        with open(sub_path, "r", encoding="utf-8") as f:
            subs = json.load(f)
        intro_sec = float(subs.get("intro_duration_sec", 25.0))
        vinheta_sec = float(subs.get("vinheta_duration_sec", 3.0))
        rest_sec = float(subs.get("rest_duration_sec", 120.0))
        lines = ["⏱️ CAPÍTULOS DO EPISÓDIO:", f"00:00 - {scenes[0].get('headline', 'Introdução').title()}"]
        if len(scenes) > 1:
            t_cur = intro_sec + vinheta_sec
            step = rest_sec / max(len(scenes) - 1, 1)
            for idx, sc in enumerate(scenes[1:]):
                total_s = int(round(t_cur + idx * step))
                mm, ss = divmod(total_s, 60)
                lines.append(f"{mm:02d}:{ss:02d} - {sc.get('headline', f'Capítulo {idx+2}').title()}")
        return "\n".join(lines) + "\n"
    except Exception:
        return ""


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
    title_candidates = seo.get("title_options", []) + [data.get("title", f"Vídeo {project_id}")]
    raw_title = title_candidates[0]
    for cand in title_candidates:
        if cand and len(cand.strip()) <= 100:
            raw_title = cand.strip()
            break
    if len(raw_title) > 100:
        raw_title = raw_title[:97].rsplit(" ", 1)[0].rstrip(":,- ") + "..."

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
        chapters_block = _build_chapters_text(project_dir, data)
        social_footer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚛️ ACOMPANHE O SCAPATICI TECNOLOGIA:\n"
            "🔔 Inscreva-se aqui no YouTube e ative o sininho!\n"
            "📱 Instagram & TikTok (3 episódios verticais todo dia): @scapatici.tecnologia\n"
            "💬 Qual teoria você achou mais surpreendente? Comente abaixo!"
        )
        base_desc = seo.get("description", "")
        if chapters_block and "CAPÍTULOS" not in base_desc.upper():
            description = f"{base_desc}\n\n{chapters_block}{social_footer}"
        else:
            description = f"{base_desc}{social_footer}"
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

    # Se for Vídeo Longo (16x9), posta comentário fixado de debate para estimular engajamento
    if video_format == "16x9":
        try:
            topic_label = data.get("topic", title)
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": (
                                    f"⚛️ E você, o que acha sobre {topic_label[:120]}?\n"
                                    "💬 Deixe sua opinião ou teoria aqui embaixo — respondo os comentários e os melhores temas viram próximos episódios!\n\n"
                                    "🔔 Inscreva-se no canal Scapatici Tecnologia e siga @scapatici.tecnologia no Instagram e TikTok!"
                                )
                            }
                        }
                    }
                }
            ).execute()
            print("[YOUTUBE] 💬 Comentário inicial de engajamento publicado no vídeo principal!")
        except Exception as mc_err:
            print(f"[YOUTUBE] ℹ️ Comentário no vídeo 16:9: {mc_err}")

    # Se for Vídeo Longo (16x9), verifica se o Shorts já foi postado e atualiza o link nele
    if video_format == "16x9":
        shorts_info_path = os.path.join(project_dir, "youtube_shorts_info.json")
        if os.path.exists(shorts_info_path):
            try:
                with open(shorts_info_path, "r", encoding="utf-8") as sf:
                    shorts_id = json.load(sf).get("video_id")
                if shorts_id:
                    print(f"[YOUTUBE] 🔄 Sincronizando link do vídeo longo no Shorts ({shorts_id})...")
                    # Atualiza descrição do Shorts
                    try:
                        s_vid = youtube.videos().list(part="snippet", id=shorts_id).execute()
                        if s_vid.get("items"):
                            s_snippet = s_vid["items"][0]["snippet"]
                            if video_url not in s_snippet["description"]:
                                s_snippet["description"] = f"🚀 ASSISTA AO VÍDEO COMPLETO: {video_url}\n\n" + s_snippet["description"]
                                youtube.videos().update(part="snippet", body={"id": shorts_id, "snippet": s_snippet}).execute()
                                print("[YOUTUBE] ✅ Descrição do Shorts atualizada com o link do vídeo longo!")
                    except Exception as sde:
                        print(f"[YOUTUBE] ⚠️ Aviso ao atualizar descrição do Shorts: {sde}")

                    # Tenta postar comentário no Shorts
                    try:
                        youtube.commentThreads().insert(
                            part="snippet",
                            body={
                                "snippet": {
                                    "videoId": shorts_id,
                                    "topLevelComment": {
                                        "snippet": {
                                            "textOriginal": f"🚀 Assista ao documentário completo em alta definição aqui:\n👉 {video_url}\n\nInscreva-se no canal Scapatici Tecnologia!"
                                        }
                                    }
                                }
                            }
                        ).execute()
                        print("[YOUTUBE] ✅ Comentário com link postado no Shorts com sucesso!")
                    except Exception as sce:
                        print(f"[YOUTUBE] ℹ️ Comentário no Shorts: {sce}")
            except Exception as e:
                print(f"[YOUTUBE] ⚠️ Falha na sincronização com Shorts: {e}")

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
    parser.add_argument("--thumb-only", action="store_true", help="Apenas atualiza a thumbnail de um vídeo já publicado")

    args = parser.parse_args()

    if args.auth_only:
        get_authenticated_service(force_reauth=True)
        print("[AUTH] Autenticação concluída com sucesso (incluindo permissão para comentários no Shorts).")
        return

    if args.thumb_only:
        project_dir = os.path.join("projects", args.project)
        info_file = os.path.join(project_dir, f"youtube_{args.format}_info.json")
        thumb_path = os.path.join(project_dir, "thumbnail.jpg")
        if not os.path.exists(info_file):
            print(f"[ERRO] {info_file} não encontrado.")
            sys.exit(1)
        with open(info_file, "r", encoding="utf-8") as f:
            video_id = json.load(f).get("video_id")
        youtube = get_authenticated_service()
        upload_thumbnail(youtube, video_id, thumb_path)
        return

    vid = upload_video(args.project, privacy_status=args.privacy, video_format=args.format)
    if not vid:
        sys.exit(1)

if __name__ == "__main__":
    main()
