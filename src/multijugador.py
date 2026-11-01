"""
Multijugador en línea / red (Carrera competitiva 1 vs 1 en vivo) usando
únicamente la librería estándar de Python (`socket`, `threading`, `json`).

Cómo funciona:
- El Anfitrión (Host) crea una sala. El sistema abre un socket TCP en un puerto
  a partir de `PUERTO_BASE` (54321), genera un código corto de 4 caracteres y
  escucha también por UDP (en localhost y broadcast LAN) para que otro jugador
  pueda unirse escribiendo solo el código de 4 caracteres (o una IP directa).
- Durante la partida, ambos jugadores intercambian su estado cada ~0.35 s
  (regiones conquistadas, usuarios, dinero, bienestar, ronda) sin bloquear el
  hilo gráfico de Pygame.
- El primero en conquistar las 8 regiones del planeta gana la carrera 1 vs 1;
  si un jugador cae en quiebra o éxodo de usuarios, el otro gana por resistencia.
"""

import json
import os
import socket
import subprocess
import sys
import threading

PUERTO_BASE = 54321
PUERTO_DESCUBRIMIENTO = 54320
INTERVALO_SYNC = 0.35
ALFABETO_CODIGO = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # 34 símbolos legibles (sin I ni O)


def obtener_ip_local():
    """Devuelve la IP de red local de la máquina (o '127.0.0.1' si no hay red)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def codificar_sala(ip, puerto):
    """Genera un código corto de 4 caracteres a partir de los últimos dos
    octetos de la IP y el desplazamiento del puerto."""
    partes = ip.split(".")
    try:
        oct2 = int(partes[2]) if len(partes) == 4 else 0
        oct3 = int(partes[3]) if len(partes) == 4 else 1
    except ValueError:
        oct2, oct3 = 0, 1
    offset = max(0, min(9, puerto - PUERTO_BASE))
    valor = ((oct2 & 0xFF) << 12) | ((oct3 & 0xFF) << 4) | (offset & 0x0F)
    base = len(ALFABETO_CODIGO)
    chars = []
    for _ in range(4):
        chars.append(ALFABETO_CODIGO[valor % base])
        valor //= base
    return "".join(reversed(chars))


def decodificar_sala(codigo, ip_referencia=None):
    """Reconstruye `(ip_estimada, puerto)` a partir de un código de 4 caracteres.
    Devuelve `(None, None)` si el código no tiene el formato válido."""
    limpio = codigo.strip().upper()
    if len(limpio) != 4 or any(c not in ALFABETO_CODIGO for c in limpio):
        return None, None
    base = len(ALFABETO_CODIGO)
    valor = 0
    for c in limpio:
        valor = valor * base + ALFABETO_CODIGO.index(c)
    offset = valor & 0x0F
    oct3 = (valor >> 4) & 0xFF
    oct2 = (valor >> 12) & 0xFF
    puerto = PUERTO_BASE + offset
    if ip_referencia is None:
        ip_referencia = obtener_ip_local()
    partes = ip_referencia.split(".")
    if len(partes) == 4 and partes[0] != "127":
        ip = f"{partes[0]}.{partes[1]}.{oct2}.{oct3}"
    else:
        ip = "127.0.0.1"
    return ip, puerto


class GestorMultijugador:
    def __init__(self):
        self.rol = None               # "host" | "cliente" | None
        self.activo = False           # True cuando hay sala creada o intentando conectar
        self.conectado = False        # True cuando ambos jugadores están enlazados
        self.partida_iniciada = False
        self.codigo_sala = ""
        self.ip_local = obtener_ip_local()
        self.puerto = PUERTO_BASE
        self.mensaje_estado = "Elige Crear Sala o escribe el código de tu rival."
        self.codigo_entrada = ""      # texto que escribe el jugador para unirse
        self.estado_rival = self._estado_rival_vacio()
        self._evento_fin_remoto = None  # ("victoria_rival", motivo) o ("colapso_rival", motivo)
        self._iniciar_remoto = False

        self._sock_servidor = None
        self._sock_conexion = None
        self._sock_udp = None
        self._cerrando = False
        self._lock = threading.Lock()
        self._timer_sync = 0.0

    @staticmethod
    def _estado_rival_vacio():
        return {
            "ronda": 1,
            "dinero": 10000,
            "usuarios": 500,
            "bienestar": 70,
            "reputacion": 70,
            "regiones": 1,
            "total_regiones": 8,
            "lista_regiones": ["sudamerica"],
            "terminada": False,
            "resultado": None,
        }

    # ---------------------------------------------------- creación y conexión

    def crear_sala(self):
        """Abre un servidor TCP en segundo plano y genera el código de 4 letras."""
        self.cerrar()
        self._cerrando = False
        self.ip_local = obtener_ip_local()

        servidor = None
        puerto_elegido = PUERTO_BASE
        for offset in range(10):
            cand = PUERTO_BASE + offset
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", cand))
                s.listen(1)
                s.settimeout(0.5)
                servidor = s
                puerto_elegido = cand
                break
            except OSError:
                s.close()

        if servidor is None:
            self.mensaje_estado = "No se pudo abrir un puerto local para la sala."
            return False

        self._sock_servidor = servidor
        self.puerto = puerto_elegido
        self.rol = "host"
        self.activo = True
        self.conectado = False
        self.partida_iniciada = False
        self.estado_rival = self._estado_rival_vacio()
        self.codigo_sala = codificar_sala(self.ip_local, self.puerto)
        self.mensaje_estado = f"Sala creada ({self.codigo_sala}). Esperando al Jugador 2..."

        threading.Thread(target=self._hilo_aceptar, daemon=True).start()
        threading.Thread(target=self._hilo_responder_udp, daemon=True).start()
        return True

    def abrir_segunda_ventana(self):
        """Si aún no hay sala activa, la crea y lanza una segunda ventana del
        juego en este mismo PC para probar el 1 vs 1 fácilmente."""
        if not (self.rol == "host" and self.activo):
            self.crear_sala()
        ruta_main = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        if os.path.isfile(ruta_main):
            try:
                subprocess.Popen([sys.executable, ruta_main])
                self.mensaje_estado = f"Sala {self.codigo_sala} lista. En la 2ª ventana pulsa «Buscar Sala Automáticamente»."
                return True
            except OSError:
                pass
        return False

    def unirse_sala(self, texto_codigo):
        """Se conecta en segundo plano usando un código de 4 caracteres o IP[:puerto]."""
        limpio = texto_codigo.strip()
        if not limpio:
            self.mensaje_estado = "Escribe primero el código de la sala (ej. 4 letras)."
            return False

        self.cerrar()
        self._cerrando = False
        self.rol = "cliente"
        self.activo = True
        self.conectado = False
        self.partida_iniciada = False
        self.estado_rival = self._estado_rival_vacio()
        self.codigo_sala = limpio.upper()
        self.mensaje_estado = f"Buscando sala {self.codigo_sala}..."

        threading.Thread(target=self._hilo_conectar, args=(limpio,), daemon=True).start()
        return True

    def iniciar_carrera(self):
        """El Host (o cualquiera ya conectado) lanza el inicio simultáneo de la partida."""
        if not self.conectado:
            return False
        self.partida_iniciada = True
        self._enviar_json({"tipo": "iniciar"})
        return True

    # --------------------------------------------------------- hilos de red

    def _hilo_aceptar(self):
        while not self._cerrando and self._sock_servidor is not None:
            try:
                conn, addr = self._sock_servidor.accept()
                conn.settimeout(1.0)
                with self._lock:
                    self._sock_conexion = conn
                    self.conectado = True
                    self.mensaje_estado = f"¡Rival conectado desde {addr[0]}! Pulsa Iniciar Carrera."
                self._bucle_recepcion(conn)
                break
            except socket.timeout:
                continue
            except OSError:
                break

    def _hilo_responder_udp(self):
        """Escucha consultas UDP en el puerto de descubrimiento para conectar
        instantáneamente tanto en la misma PC (127.0.0.1) como en la red LAN."""
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp.bind(("0.0.0.0", PUERTO_DESCUBRIMIENTO))
            udp.settimeout(0.5)
            self._sock_udp = udp
        except OSError:
            udp.close()
            return

        while not self._cerrando and not self.conectado:
            try:
                datos, addr = udp.recvfrom(256)
                texto = datos.decode("utf-8", errors="ignore").strip()
                if texto in (f"SNB_BUSCAR:{self.codigo_sala}", "SNB_BUSCAR:*"):
                    respuesta = f"SNB_AQUI:{self.codigo_sala}:{self.puerto}".encode("utf-8")
                    udp.sendto(respuesta, addr)
            except socket.timeout:
                continue
            except OSError:
                break

    def _descubrir_por_udp(self, codigo):
        """Intenta localizar la IP y puerto del Host por UDP en localhost y LAN."""
        consulta = f"SNB_BUSCAR:{codigo.upper()}".encode("utf-8")
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp.settimeout(0.35)
        try:
            for destino in ("127.0.0.1", "255.255.255.255"):
                try:
                    udp.sendto(consulta, (destino, PUERTO_DESCUBRIMIENTO))
                except OSError:
                    pass
            datos, addr = udp.recvfrom(256)
            partes = datos.decode("utf-8", errors="ignore").strip().split(":")
            if len(partes) == 3 and partes[0] == "SNB_AQUI":
                return addr[0], int(partes[2])
        except OSError:
            pass
        finally:
            udp.close()
        return None, None

    def _hilo_conectar(self, entrada):
        candidatos = []
        if "." in entrada:
            if ":" in entrada:
                host, p_str = entrada.rsplit(":", 1)
                try:
                    candidatos.append((host.strip(), int(p_str)))
                except ValueError:
                    candidatos.append((host.strip(), PUERTO_BASE))
            else:
                candidatos.append((entrada.strip(), PUERTO_BASE))
        else:
            ip_udp, p_udp = self._descubrir_por_udp(entrada)
            if ip_udp is not None:
                candidatos.append((ip_udp, p_udp))
            ip_dec, p_dec = decodificar_sala(entrada, self.ip_local)
            if ip_dec is not None:
                candidatos.append((ip_dec, p_dec))
                candidatos.append(("127.0.0.1", p_dec))
            for offset in range(3):
                candidatos.append(("127.0.0.1", PUERTO_BASE + offset))

        conectado_ok = False
        for host, puerto in candidatos:
            if self._cerrando:
                return
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.2)
            try:
                s.connect((host, puerto))
                s.settimeout(1.0)
                with self._lock:
                    self._sock_conexion = s
                    self.conectado = True
                    self.puerto = puerto
                    self.mensaje_estado = f"¡Conectado a la sala {self.codigo_sala}! Esperando inicio..."
                conectado_ok = True
                self._bucle_recepcion(s)
                break
            except OSError:
                s.close()

        if not conectado_ok and not self._cerrando:
            self.mensaje_estado = f"No se encontró la sala «{entrada.upper()}». Verifica el código."

    def _bucle_recepcion(self, sock):
        buffer = ""
        while not self._cerrando:
            try:
                trozo = sock.recv(2048)
                if not trozo:
                    if not self._cerrando:
                        self.conectado = False
                        self.mensaje_estado = "El rival se desconectó."
                    break
                buffer += trozo.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    if linea.strip():
                        self._procesar_mensaje(linea.strip())
            except socket.timeout:
                continue
            except OSError:
                if not self._cerrando:
                    self.conectado = False
                    self.mensaje_estado = "Conexión finalizada."
                break

    def _procesar_mensaje(self, linea):
        try:
            msg = json.loads(linea)
        except ValueError:
            return
        tipo = msg.get("tipo")
        if tipo == "iniciar":
            self._iniciar_remoto = True
        elif tipo == "estado":
            datos = msg.get("datos", {})
            with self._lock:
                self.estado_rival.update(datos)
                if datos.get("terminada"):
                    res = datos.get("resultado")
                    if res == "victoria":
                        self._evento_fin_remoto = ("victoria_rival", res)
                    elif res:
                        self._evento_fin_remoto = ("colapso_rival", res)

    def _enviar_json(self, obj):
        with self._lock:
            sock = self._sock_conexion
        if sock is None:
            return
        try:
            datos = (json.dumps(obj) + "\n").encode("utf-8")
            sock.sendall(datos)
        except OSError:
            pass

    # ------------------------------------------------ sincronización con Juego

    def construir_paquete_estado(self, juego):
        return {
            "ronda": juego.rondas.numero,
            "dinero": int(round(juego.recursos.dinero)),
            "usuarios": int(round(juego.recursos.usuarios)),
            "bienestar": int(round(juego.recursos.bienestar)),
            "reputacion": int(round(juego.recursos.reputacion)),
            "regiones": len(juego.mundo.conquistadas()),
            "total_regiones": len(juego.mundo.regiones),
            "lista_regiones": list(juego.mundo.conquistadas()),
            "terminada": bool(juego.rondas.terminada),
            "resultado": juego.rondas.resultado,
        }

    def enviar_estado_inmediato(self, juego):
        if self.conectado:
            self._enviar_json({"tipo": "estado", "datos": self.construir_paquete_estado(juego)})

    def actualizar(self, dt, juego):
        """Sincroniza periódicamente y devuelve acciones remotas pendientes."""
        if self._iniciar_remoto:
            self._iniciar_remoto = False
            self.partida_iniciada = True
            return "iniciar_partida"

        if not self.conectado or not self.partida_iniciada:
            return None

        self._timer_sync += dt
        if self._timer_sync >= INTERVALO_SYNC:
            self._timer_sync = 0.0
            self.enviar_estado_inmediato(juego)

        with self._lock:
            evento = self._evento_fin_remoto
            self._evento_fin_remoto = None
        return evento

    def cerrar(self):
        self._cerrando = True
        self.conectado = False
        self.partida_iniciada = False
        self.activo = False
        with self._lock:
            for s in (self._sock_conexion, self._sock_servidor, self._sock_udp):
                if s is not None:
                    try:
                        s.close()
                    except OSError:
                        pass
            self._sock_conexion = None
            self._sock_servidor = None
            self._sock_udp = None
