"""
Simple-Tube Pre-Flight Health Check & Pre-Render Buffer
Executado preventivamente às 08:30 (ou sob demanda) para garantir:
  1. Renovação proativa de credenciais/tokens (YouTube OAuth, Instagram, TikTok).
  2. Estoque mínimo de pautas para 7 dias (09h, 16h e 20h) via leitor de tendências.
  3. Pré-renderização dos vídeos do dia para publicação exata na janela de pico.
"""

import os
import sys
import json
import time
import argparse
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(PIPELINE_DIR)
PUB_DIR = os.path.join(PIPELINE_DIR, "publishing")
ALERT_FILE = os.path.join(PIPELINE_DIR, "health_alert.json")
STATUS_FILE = os.path.join(PIPELINE_DIR, "health_status.json")


def check_youtube_token() -> dict:
    token_path = os.path.join(PUB_DIR, "token.json")
    if not os.path.exists(token_path):
        return {"ok": False, "detail": "token.json não encontrado"}
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials.from_authorized_user_file(token_path)
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        if creds.valid:
            scopes = getattr(creds, "scopes", []) or []
            has_comments = "https://www.googleapis.com/auth/youtube.force-ssl" in scopes
            return {"ok": True, "comments_scope": has_comments, "detail": "Token YouTube válido e renovado"}
        return {"ok": False, "detail": "Credenciais inválidas após tentativa de renovação"}
    except Exception as e:
        return {"ok": False, "detail": f"Erro no token YouTube: {e}"}


def check_instagram_session() -> dict:
    creds_path = os.path.join(PUB_DIR, "instagram_credentials.json")
    sess_path = os.path.join(PUB_DIR, "instagram_session.json")
    if not os.path.exists(creds_path) and not os.path.exists(sess_path):
        return {"ok": False, "detail": "Credenciais/sessão do Instagram ausentes"}
    return {"ok": True, "has_cache": os.path.exists(sess_path), "detail": "Credenciais Instagram configuradas"}


def check_tiktok_session() -> dict:
    sess_path = os.path.join(PUB_DIR, "tiktok_session.json")
    if not os.path.exists(sess_path):
        return {"ok": False, "detail": "tiktok_session.json não encontrado"}
    try:
        with open(sess_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cookies = data.get("cookies", [])
        now = time.time()
        sid_cookies = [c for c in cookies if c.get("name") in ("sessionid", "sessionid_ss", "sid_tt") and c.get("value")]
        if not sid_cookies:
            return {"ok": False, "detail": "Cookie sessionid ausente em tiktok_session.json"}
        expired = [c["name"] for c in sid_cookies if c.get("expires", -1) > 0 and c["expires"] < now]
        if len(expired) == len(sid_cookies):
            return {"ok": False, "detail": f"Cookies TikTok expirados: {expired}"}
        return {"ok": True, "detail": f"{len(sid_cookies)} cookie(s) de sessão TikTok ativos"}
    except Exception as e:
        return {"ok": False, "detail": f"Erro ao validar tiktok_session.json: {e}"}


def run_health_check(pre_render: bool = False) -> bool:
    print("=" * 60, flush=True)
    print("🩺 SIMPLE-TUBE PRE-FLIGHT HEALTH CHECK", flush=True)
    print("=" * 60, flush=True)

    yt = check_youtube_token()
    ig = check_instagram_session()
    tt = check_tiktok_session()

    print(f"  [YouTube OAuth]   {'✅' if yt['ok'] else '❌'} {yt['detail']}", flush=True)
    print(f"  [Instagram Reels] {'✅' if ig['ok'] else '❌'} {ig['detail']}", flush=True)
    print(f"  [TikTok Studio]   {'✅' if tt['ok'] else '❌'} {tt['detail']}", flush=True)

    # Garante filas abastecidas (09h e TikTok 16h/20h)
    sys.path.insert(0, PIPELINE_DIR)
    sys.path.insert(0, PUB_DIR)
    import daily_autopilot as da
    import tiktok_slots_manager as tsm
    import trend_replenisher as tr

    state = da.load_state()
    pending_daily = da._get_ordered_queue(state)
    print(f"  [Fila 09h]        ✅ {len(pending_daily)} episódio(s) pronto(s) na fila", flush=True)

    tt_state = tsm.load_state()
    tt_pub = set(tt_state.get("published_topics", []))
    tt_dyn = tr.load_generated_tiktok_queue()
    need_tt_refill = False
    for sl in ("16h", "20h"):
        rem = [c for c in tsm.TIKTOK_EXCLUSIVE_SLOTS.get(sl, []) + tt_dyn.get(sl, []) if c["id"] not in tt_pub]
        if len(rem) < 3:
            need_tt_refill = True
        print(f"  [Fila TikTok {sl}] ✅ {len(rem)} tema(s) inédito(s) disponível(is)", flush=True)
    if need_tt_refill:
        tr.replenish_tiktok_slots_queue(tt_pub, tsm.TIKTOK_EXCLUSIVE_SLOTS, days=7)

    report = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "youtube": yt,
        "instagram": ig,
        "tiktok": tt,
        "daily_queue_count": len(pending_daily),
    }
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    alerts = {k: v for k, v in [("youtube", yt), ("instagram", ig), ("tiktok", tt)] if not v["ok"]}
    if alerts:
        with open(ALERT_FILE, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2, ensure_ascii=False)
    elif os.path.exists(ALERT_FILE):
        try:
            os.remove(ALERT_FILE)
        except Exception:
            pass

    if pre_render:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "AUTOPILOT_UNATTENDED": "1"}
        print("\n⚡ Executando pré-renderização preventiva para os horários de pico...", flush=True)
        subprocess.run("python pipeline/daily_autopilot.py --prepare-only", shell=True, cwd=PROJECT_DIR, env=env)
        subprocess.run("python pipeline/publishing/tiktok_slots_manager.py --slot 16h --prepare-only", shell=True, cwd=PROJECT_DIR, env=env)
        subprocess.run("python pipeline/publishing/tiktok_slots_manager.py --slot 20h --prepare-only", shell=True, cwd=PROJECT_DIR, env=env)

    print("=" * 60, flush=True)
    return not bool(alerts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple-Tube Pre-Flight Health Check")
    parser.add_argument("--pre-render", action="store_true", help="Pré-renderiza os episódios do dia antes dos horários de publicação")
    args = parser.parse_args()
    ok = run_health_check(pre_render=args.pre_render)
    if not ok:
        sys.exit(1)

