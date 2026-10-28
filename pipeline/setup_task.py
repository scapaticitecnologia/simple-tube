import subprocess
import re
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_DIR)

cmd_export = 'schtasks /query /tn "SimpleTube-DailyProduction" /xml'
res = subprocess.run(cmd_export, shell=True, capture_output=True)

raw = res.stdout
text = None
for enc in ['utf-16le', 'utf-16', 'utf-8', 'cp1252']:
    try:
        decoded = raw.decode(enc)
        if '<Task' in decoded:
            text = decoded
            break
    except Exception:
        continue

if not text or '<Task' not in text:
    print('Failed to decode XML:', raw[:200])
    sys.exit(1)

# Habilita StartWhenAvailable = true (executa assim que ligar caso o horário tenha passado)
if '<StartWhenAvailable>' in text:
    text = re.sub(r'<StartWhenAvailable>.*?</StartWhenAvailable>', '<StartWhenAvailable>true</StartWhenAvailable>', text)
else:
    text = text.replace('<Settings>', '<Settings>\n    <StartWhenAvailable>true</StartWhenAvailable>')

# Habilita execução na bateria
text = re.sub(r'<DisallowStartIfOnBatteries>.*?</DisallowStartIfOnBatteries>', '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>', text)
text = re.sub(r'<StopIfGoingOnBatteries>.*?</StopIfGoingOnBatteries>', '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>', text)

# Adiciona o LogonTrigger para rodar ao inicializar/fazer login caso a máquina estivesse desligada
if '<LogonTrigger>' not in text:
    logon_trigger = '    <LogonTrigger>\n      <Enabled>true</Enabled>\n    </LogonTrigger>'
    text = text.replace('</Triggers>', f'{logon_trigger}\n  </Triggers>')

xml_path = os.path.join(PROJECT_DIR, 'pipeline', 'task_definition.xml')
with open(xml_path, 'w', encoding='utf-16') as f:
    f.write(text)

cmd_import = f'schtasks /create /tn "SimpleTube-DailyProduction" /xml "{xml_path}" /f'
res_imp = subprocess.run(cmd_import, shell=True, capture_output=True, text=True)

print("Status Import:", res_imp.stdout.strip() or res_imp.stderr.strip())
print(f"Arquivo XML de configuracao: {xml_path}")
