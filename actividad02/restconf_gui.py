import json
import threading
import ipaddress
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import quote

import requests

requests.packages.urllib3.disable_warnings()

DEFAULT_HOST = "10.10.20.48"
DEFAULT_USER = "developer"
DEFAULT_PASS = "C1sco12345"

HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-type": "application/yang-data+json",
}
TIMEOUT = 10

# Interfaz de management del sandbox: NO modificar ni borrar
PROTECTED = {"gigabitethernet1"}

GREEN = "#2e7d32"
RED = "#c62828"
ORANGE = "#ef6c00"
GRAY = "#555555"


class RestconfApp:
    def __init__(self, root):
        self.root = root
        root.title("Cliente RESTCONF - IOS XE")
        root.geometry("640x640")
        root.minsize(600, 600)

        self.buttons = []
        self._build_connection_frame()
        self._build_form_frame()
        self._build_buttons_frame()
        self._build_result_frame()
        self._build_status_bar()

        self.set_status("Listo", GRAY)

    # ---------------- Interfaz ----------------
    def _build_connection_frame(self):
        frame = ttk.LabelFrame(self.root, text="Conexión (Basic Auth)")
        frame.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(frame, text="Host:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.host_var = tk.StringVar(value=DEFAULT_HOST)
        ttk.Entry(frame, textvariable=self.host_var, width=18).grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="Usuario:").grid(row=0, column=2, sticky="e", padx=5)
        self.user_var = tk.StringVar(value=DEFAULT_USER)
        ttk.Entry(frame, textvariable=self.user_var, width=14).grid(row=0, column=3, padx=5)

        ttk.Label(frame, text="Password:").grid(row=0, column=4, sticky="e", padx=5)
        self.pass_var = tk.StringVar(value=DEFAULT_PASS)
        ttk.Entry(frame, textvariable=self.pass_var, show="*", width=14).grid(row=0, column=5, padx=5)

    def _build_form_frame(self):
        frame = ttk.LabelFrame(self.root, text="Interfaz")
        frame.pack(fill="x", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.name_entry = ttk.Entry(frame)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.name_entry.insert(0, "Loopback99")

        ttk.Label(frame, text="Dirección IP:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.ip_entry = ttk.Entry(frame)
        self.ip_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.ip_entry.insert(0, "99.99.99.99")

        ttk.Label(frame, text="Máscara:").grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.mask_entry = ttk.Entry(frame)
        self.mask_entry.grid(row=2, column=1, sticky="ew", padx=5)
        self.mask_entry.insert(0, "255.255.255.0")

        ttk.Label(frame, text="Descripción:").grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.desc_entry = ttk.Entry(frame)
        self.desc_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=(0, 5))
        self.desc_entry.insert(0, "WHATEVER99")

    def _build_buttons_frame(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", padx=10, pady=5)

        b1 = ttk.Button(frame, text="Consultar Interfaz", command=self.on_get)
        b2 = ttk.Button(frame, text="Crear/Actualizar Interfaz", command=self.on_put)
        b3 = ttk.Button(frame, text="Eliminar Interfaz", command=self.on_delete)
        for b in (b1, b2, b3):
            b.pack(side="left", expand=True, fill="x", padx=3)
            self.buttons.append(b)

    def _build_result_frame(self):
        frame = ttk.LabelFrame(self.root, text="Resultado")
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(frame, columns=("campo", "valor"), show="headings", height=10)
        self.tree.heading("campo", text="Campo")
        self.tree.heading("valor", text="Valor")
        self.tree.column("campo", width=150, anchor="w")
        self.tree.column("valor", width=400, anchor="w")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scroll.pack(side="right", fill="y", pady=5)

    def _build_status_bar(self):
        self.status = tk.Label(
            self.root, text="", anchor="w", fg="white", bg=GRAY,
            font=("TkDefaultFont", 10, "bold"), padx=10, pady=6,
        )
        self.status.pack(side="bottom", fill="x")

    # ---------------- Utilidades ----------------
    def set_status(self, text, color):
        self.status.config(text=text, bg=color)

    def set_busy(self, busy):
        state = "disabled" if busy else "normal"
        for b in self.buttons:
            b.config(state=state)

    def show_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for campo, valor in rows:
            self.tree.insert("", "end", values=(campo, valor))

    def get_name(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Falta dato", "Escribe el nombre de la interfaz.")
            return None
        return name

    def is_protected(self, name):
        if name.lower() in PROTECTED:
            messagebox.showerror(
                "Interfaz protegida",
                f"{name} es la interfaz de management del sandbox.\n"
                "No se debe modificar ni eliminar.",
            )
            return True
        return False

    def build_url(self, name):
        host = self.host_var.get().strip()
        return (
            f"https://{host}/restconf/data/"
            f"ietf-interfaces:interfaces/interface={quote(name, safe='')}"
        )

    def send(self, method, name, body=None):
        return requests.request(
            method,
            self.build_url(name),
            data=json.dumps(body) if body is not None else None,
            auth=(self.user_var.get().strip(), self.pass_var.get()),
            headers=HEADERS,
            verify=False,
            timeout=TIMEOUT,
        )

    def run_async(self, work, on_done):
        self.set_busy(True)
        self.set_status("Procesando...", ORANGE)

        def target():
            try:
                resp, error = work(), None
            except Exception as exc:
                resp, error = None, exc
            self.root.after(0, lambda: self.finish(resp, error, on_done))

        threading.Thread(target=target, daemon=True).start()

    def finish(self, resp, error, on_done):
        self.set_busy(False)
        if error is not None:
            self.handle_exception(error)
            return
        on_done(resp)

    def handle_exception(self, exc):
        if isinstance(exc, requests.exceptions.Timeout):
            msg = "Error: tiempo de espera agotado. ¿La VPN sigue conectada?"
        elif isinstance(exc, requests.exceptions.ConnectionError):
            msg = "Error de conexión: no se llega al router. Revisa host y VPN."
        else:
            msg = f"Error inesperado: {exc}"
        self.set_status(msg, RED)
        self.show_rows([])

    def error_text(self, resp):
        known = {
            400: "Petición incorrecta (revisa los datos)",
            401: "No autorizado (usuario o password incorrectos)",
            403: "Acceso prohibido",
            404: "No encontrado (la interfaz no existe)",
            409: "Conflicto con la configuración actual",
            500: "Error interno del router",
        }
        return f"Error {resp.status_code}: {known.get(resp.status_code, resp.reason)}"

    def is_ok(self, resp):
        return 200 <= resp.status_code <= 299

    # ---------------- Desafío 1: GET ----------------
    def on_get(self):
        name = self.get_name()
        if not name:
            return
        self.run_async(lambda: self.send("GET", name), self.after_get)

    def after_get(self, resp):
        if not self.is_ok(resp):
            self.set_status(self.error_text(resp), RED)
            self.show_rows([])
            return
        try:
            data = resp.json()
            iface = data["ietf-interfaces:interface"]
        except (ValueError, KeyError):
            self.set_status("Error: respuesta inesperada del router", RED)
            return

        # RESTCONF devuelve una lista con un solo elemento
        if isinstance(iface, list):
            iface = iface[0] if iface else {}

        rows = [
            ("Nombre", iface.get("name", "-")),
            ("Descripción", iface.get("description", "(sin descripción)")),
            ("Tipo", iface.get("type", "-")),
            ("Estado", "Habilitada (enabled)" if iface.get("enabled") else "Deshabilitada (disabled)"),
        ]
        addresses = iface.get("ietf-ip:ipv4", {}).get("address", [])
        if addresses:
            for i, addr in enumerate(addresses, start=1):
                suffix = f" #{i}" if len(addresses) > 1 else ""
                rows.append((f"IP{suffix}", addr.get("ip", "-")))
                rows.append((f"Máscara{suffix}", addr.get("netmask", "-")))
        else:
            rows.append(("IP", "(sin dirección IPv4)"))
            rows.append(("Máscara", "-"))
        self.show_rows(rows)

        if addresses:
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, addresses[0].get("ip", ""))
            self.mask_entry.delete(0, tk.END)
            self.mask_entry.insert(0, addresses[0].get("netmask", ""))
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, iface.get("description", ""))

        self.set_status(f"Operación exitosa (código {resp.status_code})", GREEN)

    # ---------------- Desafío 2: PUT ----------------
    def build_yang_config(self, name, ip, mask, desc):
        if name.lower().startswith("loopback"):
            if_type = "iana-if-type:softwareLoopback"
        else:
            if_type = "iana-if-type:ethernetCsmacd"

        interface = {
            "name": name,
            "type": if_type,
            "enabled": True,
            "ietf-ip:ipv4": {"address": [{"ip": ip, "netmask": mask}]},
            "ietf-ip:ipv6": {},
        }
        if desc:
            interface["description"] = desc
        return {"ietf-interfaces:interface": interface}

    def on_put(self):
        name = self.get_name()
        if not name or self.is_protected(name):
            return

        ip = self.ip_entry.get().strip()
        mask = self.mask_entry.get().strip()
        desc = self.desc_entry.get().strip()

        try:
            ipaddress.IPv4Address(ip)
            ipaddress.IPv4Address(mask)
        except ValueError:
            messagebox.showwarning("Dato inválido", "La IP o la máscara no tienen un formato IPv4 válido.")
            return

        yang_config = self.build_yang_config(name, ip, mask, desc)
        self.run_async(lambda: self.send("PUT", name, yang_config), self.after_put)

    def after_put(self, resp):
        if self.is_ok(resp):
            accion = "creada" if resp.status_code == 201 else "actualizada"
            self.set_status(f"Operación exitosa (código {resp.status_code})", GREEN)
            messagebox.showinfo("Éxito", f"Interfaz {accion} correctamente.\nCódigo HTTP: {resp.status_code}")
            self.show_rows([("Resultado", f"Interfaz {accion} ({resp.status_code})")])
        else:
            self.set_status(self.error_text(resp), RED)

    # ---------------- Desafío 3: DELETE ----------------
    def on_delete(self):
        name = self.get_name()
        if not name or self.is_protected(name):
            return

        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Seguro que quieres eliminar la interfaz {name}?\nEsta acción no se puede deshacer.",
        )
        if not confirmar:
            self.set_status("Eliminación cancelada", GRAY)
            return
        self.run_async(lambda: self.send("DELETE", name), self.after_delete)

    def after_delete(self, resp):
        if self.is_ok(resp):
            self.set_status(f"Operación exitosa (código {resp.status_code})", GREEN)
            messagebox.showinfo("Éxito", "Interfaz eliminada correctamente.")
            self.show_rows([("Resultado", f"Interfaz eliminada ({resp.status_code})")])
        else:
            self.set_status(self.error_text(resp), RED)


if __name__ == "__main__":
    root = tk.Tk()
    RestconfApp(root)
    root.mainloop()
