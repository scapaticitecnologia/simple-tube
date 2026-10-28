"""
Simple-Tube YouTube Publisher
Gerencia upload, metadados (título, descrição, tags), agendamento e thumbnails
usando a API oficial do YouTube v3 com OAuth 2.0 local.
"""

import os
import sys
import json
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def display_publish_plan(project_id: str):
    script_path = os.path.join("projects", project_id, "script.json")
    video_path_16x9 = os.path.join("projects", project_id, "output_16x9.mp4")
    video_path_shorts = os.path.join("projects", project_id, "output_shorts.mp4")

    if not os.path.exists(script_path):
        print(f"[ERRO] Roteiro não encontrado em: {script_path}")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    seo = data.get("seo", {})
    titles = seo.get("title_options", [data.get("title", "")])

    print("=" * 60)
    print(f"📦 PLANO DE PUBLICAÇÃO: {project_id}")
    print("=" * 60)
    print(f"\n🎯 Título Principal: {titles[0]}")
    if len(titles) > 1:
        print("💡 Variações para Teste A/B:")
        for idx, t in enumerate(titles[1:], 1):
            print(f"   [{idx}] {t}")

    print(f"\n📝 Descrição:\n{seo.get('description', '')}")
    print(f"\n🏷️ Tags: {', '.join(seo.get('tags', []))}")
    
    print("\n📁 Arquivos de Mídia:")
    print(f"   - Vídeo 16:9: {'[DISPONÍVEL]' if os.path.exists(video_path_16x9) else '[PENDENTE DE RENDER]'}")
    print(f"   - Vídeo Shorts: {'[DISPONÍVEL]' if os.path.exists(video_path_shorts) else '[PENDENTE DE RENDER]'}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Publisher Helper")
    parser.add_argument("--project", type=str, default="video-001-wow-signal", help="ID do projeto")
    args = parser.parse_args()
    display_publish_plan(args.project)
