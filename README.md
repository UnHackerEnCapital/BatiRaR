# 🦇 BatiRaR 
# 🧪 WinRAR C2 Lab (CVE-2025-8088 & 2025-6218)

<img width="390" height="363" alt="BatiRaR" src="https://github.com/user-attachments/assets/3b93f086-2667-4635-883f-d0c9484ea221" />

**BatiRaR** es una herramienta de seguridad ofensiva diseñada para la replicación técnica de PoC (Proof of Concept) de las vulnerabilidades de Path Traversal e Inyección de Código Remoto en WinRAR (CVE-2025-8088 y CVE-2025-6218). Su propósito principal es permitir a los profesionales de ciberseguridad auditar la resiliencia de los sistemas ante vectores de ataque que logran persistencia y control remoto mediante la extracción de archivos maliciosos.

> 🔐 **Aviso:** Esta herramienta debe utilizarse exclusivamente en entornos controlados o bajo marcos de trabajo de auditoría autorizados. La ejecución de la PoC realiza modificaciones en el inicio del sistema (Startup) para validar la efectividad de la vulnerabilidad.

### 🔍 Vulnerabilidades
- **CVE-2025-8088**: Path Traversal en el motor de descompresión.
- **CVE-2025-6218**: Vulnerabilidad de inyección de rutas.

---

## ⚙️ Componentes del Proyecto

1. **BatiRaR-Generador.py**: Automatiza la creación de un archivo `.rar` malicioso. Genera un señuelo PDF (opcional), inyecta la carga útil mediante **ADS (Alternate Data Streams)** y parchea los encabezados binarios para habilitar el Path Traversal.
2. **BatiRaR-C2.py**: Un servidor de Comando y Control (C2) interactivo que escucha conexiones y permite ejecutar comandos de PowerShell de forma remota en la víctima.

---

## 🛠️ Funcionamiento Técnico

1. **Generación**: El script crea un archivo `payload.bat` que contiene un código HTA invisible.
2. **Path Traversal**: El generador inyecta rutas relativas (`../../`) en el RAR para depositar el archivo en:
   `AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\batiRAR.bat`
3. **Persistencia**: Al iniciar sesión, el `.bat` lanza un proceso `mshta.exe` que conecta al C2 cada 10 segundos.
4. **C2**: El atacante recibe la conexión y puede enviar comandos (ej. `whoami`, `dir`, `ipconfig`) y recibir los resultados directamente en su consola.

---

## 🚀 Guía de Uso

### 1. Iniciar el C2 (Atacante)
Ejecuta el receptor para esperar la conexión de la víctima:
```bash
python BatiRaR-C2.py
```
*El servidor corre por defecto en el puerto **5454**.*

### 2. Generar el Exploit
Corre el generador en una máquina Windows (requiere WinRAR instalado):
```bash
python BatiRaR-Generador.py
```

<img width="490" height="463" alt="BatiRaR" src="https://github.com/user-attachments/assets/23ba220b-ad1c-48a2-a201-531eb4f2ae66"/> 

- Introduce la **IP** y el **Puerto** de tu C2.
- Elige entre crear un CV PDF automático o usar un archivo existente.
- Se generará el archivo: `Soporte_Tecnico_Nahuel.rar`.

### 3. Explotación
- La víctima debe extraer el archivo usando la **interfaz gráfica (GUI)** de WinRAR.
- Tras reiniciar o iniciar sesión, la conexión aparecerá en tu consola C2.

<img width="490" height="463" alt="BatiRaR" src="https://github.com/user-attachments/assets/ca6f889d-a8ed-4761-a7d5-a11e502968c9"/>

---

## 📊 Detección (VirusTotal)
En su versión base, esta técnica ha mostrado una detección baja: **14 de 62 motores**. Es ideal para pruebas de concepto en entornos de auditoría.

<img width="490" height="463" alt="BatiRaR" src="https://github.com/user-attachments/assets/7b8e1db7-baf9-4043-b9ad-e59790a7f964"/>


---

## ⚠️ Descargo de Responsabilidad
Este software se proporciona exclusivamente con fines educativos y de investigación. **Nahuel Sagardoy / UnHackerEnCapital** no se responsabiliza por el uso indebido de estas herramientas fuera de un marco legal y ético.
