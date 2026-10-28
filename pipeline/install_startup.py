import os

appdata = os.environ.get('APPDATA')
startup = os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
vbs_path = os.path.join(startup, 'SimpleTube_Startup.vbs')
bat_path = r'c:\Users\ripia\OneDrive\Documentos\projetos\simple-tube\pipeline\run_daily_autopilot.bat'

vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c ""{bat_path}""", 0, False
'''

with open(vbs_path, 'w', encoding='utf-8') as f:
    f.write(vbs_content)

print("VBS Criado com sucesso em:", vbs_path)
print("Arquivo existe:", os.path.exists(vbs_path))
