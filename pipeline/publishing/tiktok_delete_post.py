"""
Remove um post do TikTok pelo trecho do título/legenda, via TikTok Studio (sessão salva).
Uso:
  python pipeline/publishing/tiktok_delete_post.py --match "APOD" --recon   (apenas inspeciona e tira screenshot)
  python pipeline/publishing/tiktok_delete_post.py --match "APOD"           (exclui o post)
"""
import os
import sys
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
from tiktok_uploader import get_browser_instance, SESSION_FILE  # noqa: E402

SHOT_DIR = SCRIPT_DIR


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", required=True, help="Trecho do título do post a excluir")
    ap.add_argument("--recon", action="store_true")
    args = ap.parse_args()

    with sync_playwright() as p:
        browser = get_browser_instance(p, headless=False)
        context = browser.new_context(
            storage_state=SESSION_FILE,
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        page.screenshot(path=os.path.join(SHOT_DIR, "tiktok_delete_step1.png"))

        row = page.locator(f"text={args.match}").first
        if row.count() == 0:
            print(f"[DELETE] ❌ Post contendo '{args.match}' não encontrado na lista de conteúdos.")
            browser.close()
            sys.exit(2)
        print(f"[DELETE] 🔎 Post encontrado: {row.inner_text()[:120]}")

        if args.recon:
            row.hover()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(SHOT_DIR, "tiktok_delete_step2.png"))
            browser.close()
            return

        # Linha = container mais interno que contém o título e os botões de Ações
        row_el = page.locator("div", has=page.locator(f"text={args.match}")).filter(has=page.locator("button")).last
        row_el.hover()
        page.wait_for_timeout(1000)
        more_btn = row_el.locator("button, [role='button']").last
        more_btn.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOT_DIR, "tiktok_delete_step3.png"))

        delete_item = page.locator("text=/^\\s*(Excluir|Delete)\\s*$/").first
        delete_item.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOT_DIR, "tiktok_delete_step3b.png"))

        confirm = page.locator("[role='dialog'] button:has-text('Excluir'), [role='dialog'] button:has-text('Delete')").last
        if confirm.count() == 0:
            confirm = page.locator("button:has-text('Excluir'):visible").last
        confirm.click()
        page.wait_for_timeout(6000)
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        page.screenshot(path=os.path.join(SHOT_DIR, "tiktok_delete_step4.png"))
        still = page.locator(f"text={args.match}").count()
        print("[DELETE] ✅ Post removido com sucesso." if still == 0 else "[DELETE] ⚠️ O post ainda aparece na lista — verificar screenshot.")
        browser.close()
        sys.exit(0 if still == 0 else 3)


if __name__ == "__main__":
    main()
