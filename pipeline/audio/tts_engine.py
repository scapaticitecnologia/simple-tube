"""
TTS Engine para Simple-Tube
Gera áudio de narração profissional usando Edge-TTS gratuito e local,
com suporte à arquitetura: Introdução (Hook) -> Vinheta (3s) -> Restante do Vídeo.
"""

import sys
import os
import json
import asyncio
import argparse
import re
import edge_tts

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

DEFAULT_VOICE = "pt-BR-AntonioNeural"

def naturalize_text_prosody(text: str) -> str:
    """
    Otimiza o texto para máxima naturalidade e cadência humana no Edge-TTS:
    - Insere pausas de respiração e reflexão com pontuações expressivas
    - Suaviza transições antes de conjunções reflexivas
    - Garante entonação dramática de documentário científico
    """
    if not text:
        return text
    
    # Substitui pontos e vírgulas secos por pausas mais expressivas
    t = text.replace(";", " — ")
    
    # Dá mais respiração e suspense antes de conectivos reflexivos se não houver pontuação prévia
    t = re.sub(r'(\w+)\s+(mas|porém|contudo|entretanto)\s+', r'\1, \2 ', t)
    t = re.sub(r'(\w+)\s+(de repente|subitamente|inexplicavelmente)\s+', r'\1... \2 ', t)
    
    # Assegura que reticências tenham espaço após
    t = re.sub(r'\.{3,}', '... ', t)
    
    # Remove espaços duplos
    t = re.sub(r'\s+', ' ', t).strip()
    return t

async def synthesize_segment(text: str, output_audio_path: str, voice: str = DEFAULT_VOICE, rate: str = "+0%", pitch: str = "+0Hz"):
    """Sintetiza um segmento de texto com retry automático e retorna os limites de palavras e duração total."""
    os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)
    optimized_text = naturalize_text_prosody(text)

    last_err = None
    boundaries = []
    for attempt in range(1, 4):
        try:
            communicate = edge_tts.Communicate(optimized_text, voice, rate=rate, pitch=pitch)
            boundaries = []
            with open(output_audio_path, "wb") as audio_file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_file.write(chunk["data"])
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        offset_sec = chunk["offset"] / 10_000_000
                        duration_sec = chunk["duration"] / 10_000_000
                        boundaries.append({
                            "type": chunk["type"],
                            "text": chunk.get("text", ""),
                            "start": round(offset_sec, 3),
                            "end": round(offset_sec + duration_sec, 3),
                            "duration": round(duration_sec, 3)
                        })
            if os.path.exists(output_audio_path) and os.path.getsize(output_audio_path) > 512:
                last_err = None
                break
            raise RuntimeError("Arquivo de áudio gerado vazio pelo Edge-TTS.")
        except Exception as err:
            last_err = err
            wait_sec = 3 * attempt
            print(f"[TTS] ⚠️ Tentativa {attempt}/3 falhou ({err}). Repetindo em {wait_sec}s...", flush=True)
            await asyncio.sleep(wait_sec)

    if last_err is not None:
        raise last_err
                
    words_timeline = []
    for b in boundaries:
        if b["type"] == "WordBoundary":
            words_timeline.append({
                "word": b["text"],
                "start": b["start"],
                "end": b["end"],
                "duration": b["duration"]
            })
        elif b["type"] == "SentenceBoundary":
            raw_words = [w for w in re.split(r'\s+', b["text"]) if w.strip()]
            if not raw_words:
                continue
            total_chars = sum(len(w) for w in raw_words)
            current_time = b["start"]
            sentence_duration = b["duration"]
            
            for w in raw_words:
                word_dur = round((len(w) / max(total_chars, 1)) * sentence_duration, 3)
                words_timeline.append({
                    "word": w,
                    "start": round(current_time, 3),
                    "end": round(current_time + word_dur, 3),
                    "duration": word_dur
                })
                current_time += word_dur

    duration_sec = words_timeline[-1]["end"] if words_timeline else 0
    return duration_sec, words_timeline, boundaries

async def process_structured_script(script_data: dict, out_audio_path: str, out_sub_path: str, voice: str, rate: str, pitch: str, vinheta_sec: float = 3.0):
    scenes = script_data.get("scenes", [])
    if not scenes:
        print("[ERRO] Nenhuma cena encontrada no script.")
        return

    intro_scene = scenes[0]
    rest_scenes = scenes[1:]
    
    project_dir = os.path.dirname(os.path.abspath(out_audio_path))
    audio_intro_path = os.path.join(project_dir, "audio_intro.mp3")
    audio_rest_path = os.path.join(project_dir, "audio_rest.mp3")

    print("[TTS] 🎙️ Sintetizando narração da INTRODUÇÃO (Hook)...")
    intro_dur, intro_words, _ = await synthesize_segment(
        intro_scene.get("narration", ""),
        audio_intro_path,
        voice=voice, rate=rate, pitch=pitch
    )

    print(f"[TTS] ✅ Introdução gerada: {intro_dur:.2f}s ({len(intro_words)} palavras)")

    print(f"[TTS] ⚡ Vinheta do canal programada: {vinheta_sec:.2f}s de intervalo")
    rest_offset = round(intro_dur + vinheta_sec, 3)

    rest_dur = 0.0
    rest_words = []
    if rest_scenes:
        rest_text = " ".join([s.get("narration", "") for s in rest_scenes])
        print("[TTS] 🎙️ Sintetizando narração do RESTANTE DO VÍDEO...")
        raw_rest_dur, raw_rest_words, _ = await synthesize_segment(
            rest_text,
            audio_rest_path,
            voice=voice, rate=rate, pitch=pitch
        )
        rest_dur = raw_rest_dur
        
        # Desloca a timeline das palavras do restante para depois da vinheta
        for w in raw_rest_words:
            rest_words.append({
                "word": w["word"],
                "start": round(w["start"] + rest_offset, 3),
                "end": round(w["end"] + rest_offset, 3),
                "duration": w["duration"]
            })
        print(f"[TTS] ✅ Restante do vídeo gerado: {rest_dur:.2f}s ({len(rest_words)} palavras)")

    # Também gera a narração contínua completa para fallback
    full_text = " ".join([s.get("narration", "") for s in scenes if s.get("narration")])
    await synthesize_segment(full_text, out_audio_path, voice=voice, rate=rate, pitch=pitch)

    # Sintetiza o mini-documentário vertical (Shorts / Reels / TikTok ~1m40s a 1m55s)
    audio_shorts_path = os.path.join(project_dir, "audio_shorts.mp3")
    shorts_narration = script_data.get("shorts_narration", "").strip()
    if len(shorts_narration.split()) < 220 and len(scenes) > 2:
        # Constrói versão vertical densa e explicativa (~250-300 palavras / ~95s-115s) a partir dos principais atos + CTA
        core_acts = [s.get("narration", "").strip() for s in scenes[:-1] if s.get("narration", "").strip()]
        chosen_acts = []
        word_total = 0
        for act in core_acts:
            if word_total >= 245:
                break
            chosen_acts.append(act)
            word_total += len(act.split())
        shorts_cta = (
            "A investigação completa com todos os detalhes está no vídeo principal do YouTube: "
            "acesse o link fixado nos comentários e na descrição, inscreva-se no canal Scapatici Tecnologia e até o próximo vídeo!"
        )
        shorts_narration = " ".join(chosen_acts) + " " + shorts_cta

    if shorts_narration:
        print("[TTS] 📱 Sintetizando narração densa para SHORTS / REELS / TIKTOK (~1m45s)...")
        shorts_dur, shorts_words, _ = await synthesize_segment(
            shorts_narration,
            audio_shorts_path,
            voice=voice, rate=rate, pitch=pitch
        )
        print(f"[TTS] ✅ Áudio Vertical Denso gerado: {shorts_dur:.2f}s ({len(shorts_words)} palavras)")
    else:
        import shutil
        shutil.copyfile(audio_intro_path, audio_shorts_path)
        shorts_dur = intro_dur
        shorts_words = intro_words

    # Combina timelines para o vídeo 16:9
    combined_timeline = intro_words + rest_words
    total_duration_sec = round(intro_dur + vinheta_sec + rest_dur, 3)

    subtitles_payload = {
        "voice": voice,
        "rate": rate,
        "pitch": pitch,
        "intro_duration_sec": intro_dur,
        "vinheta_duration_sec": vinheta_sec,
        "rest_duration_sec": rest_dur,
        "shorts_duration_sec": shorts_dur,
        "total_duration_sec": total_duration_sec,
        "total_words": len(combined_timeline),
        "timeline": combined_timeline,
        "shorts_timeline": shorts_words
    }

    if out_sub_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_sub_path)), exist_ok=True)
        with open(out_sub_path, "w", encoding="utf-8") as f:
            json.dump(subtitles_payload, f, indent=2, ensure_ascii=False)
        print(f"[TTS] 📄 Subtitles salvos com precisão em: {out_sub_path}")

    print(f"[TTS] 🎬 Estrutura concluída:")
    print(f"       - Introdução: {intro_dur:.2f}s")
    print(f"       - Vinheta:    {vinheta_sec:.2f}s")
    print(f"       - Restante:   {rest_dur:.2f}s")
    print(f"       - Duração Total: {total_duration_sec:.2f}s")

def main():
    parser = argparse.ArgumentParser(description="Simple-Tube TTS Generator")
    parser.add_argument("--text", type=str, help="Texto direto a narrar")
    parser.add_argument("--file", type=str, help="Caminho do arquivo .txt ou .json com o texto")
    parser.add_argument("--out-audio", type=str, required=True, help="Caminho do arquivo .mp3 de saída")
    parser.add_argument("--out-sub", type=str, help="Caminho do arquivo .json ou .srt de saída com os timings")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help="Voz (default: pt-BR-AntonioNeural)")
    parser.add_argument("--rate", type=str, default="+0%", help="Velocidade (ex: +0%, -2%)")
    parser.add_argument("--pitch", type=str, default="+0Hz", help="Tom/Pitch (ex: +0Hz, -1Hz)")
    parser.add_argument("--vinheta-sec", type=float, default=3.0, help="Duração da vinheta em segundos")
    
    args = parser.parse_args()
    
    if args.file and args.file.endswith(".json"):
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "scenes" in data:
            asyncio.run(process_structured_script(
                data, args.out_audio, args.out_sub,
                voice=args.voice, rate=args.rate, pitch=args.pitch,
                vinheta_sec=args.vinheta_sec
            ))
            return

    # Fallback para texto plano
    content = ""
    if args.text:
        content = args.text
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

    async def simple_run():
        dur, words, bounds = await synthesize_segment(content, args.out_audio, voice=args.voice, rate=args.rate, pitch=args.pitch)
        if args.out_sub:
            with open(args.out_sub, "w", encoding="utf-8") as f:
                json.dump({
                    "voice": args.voice,
                    "rate": args.rate,
                    "pitch": args.pitch,
                    "total_duration_sec": dur,
                    "total_words": len(words),
                    "timeline": words
                }, f, indent=2, ensure_ascii=False)

    asyncio.run(simple_run())

if __name__ == "__main__":
    main()

