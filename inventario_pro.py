import os
import sys
import csv
import sqlite3
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path

APP_NAME = "InventarioPro"
APP_VERSION = "1.0.0"

def data_dir():
    root = os.environ.get("LOCALAPPDATA") or str(Path.home())
    path = Path(root) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

DB_PATH = data_dir() / "inventario.db"

def money(value):
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "$0.00"

class InventoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} | Sistema de inventarios")
        self.geometry("1250x760")
        self.minsize(1050, 650)
        self.configure(bg="#F3F6FB")
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.init_db()
        self.setup_style()
        self.build_layout()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT NOT NULL UNIQUE,
                    barcode TEXT DEFAULT '',
                    name TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    supplier TEXT DEFAULT '',
                    cost REAL NOT NULL DEFAULT 0,
                    price REAL NOT NULL DEFAULT 0,
                    stock INTEGER NOT NULL DEFAULT 0,
                    min_stock INTEGER NOT NULL DEFAULT 0,
                    location TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    sku TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    movement_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    previous_stock INTEGER NOT NULL,
                    new_stock INTEGER NOT NULL,
                    note TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                )
            """)

    def setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", background="white", fieldbackground="white",
                        foreground="#172033", rowheight=31, borderwidth=0,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#EAF0F8", foreground="#34415A",
                        font=("Segoe UI Semibold", 10), relief="flat", padding=9)
        style.map("Treeview", background=[("selected", "#DCEAFE")],
                  foreground=[("selected", "#172033")])
        style.configure("TCombobox", padding=6)
        style.configure("TEntry", padding=6)

    def build_layout(self):
        self.sidebar = tk.Frame(self, bg="#17243A", width=218)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg="#17243A")
        brand.pack(fill="x", padx=20, pady=(25, 30))
        tk.Label(brand, text="▦  INVENTARIO", bg="#17243A", fg="white",
                 font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(brand, text="PRO  •  Gestión comercial", bg="#17243A", fg="#9DAFC9",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))

        self.nav_buttons = {}
        for key, label in [
            ("dashboard", "▦   Panel principal"),
            ("products", "▤   Productos"),
            ("movements", "⇄   Movimientos"),
        ]:
            b = tk.Button(self.sidebar, text=label, anchor="w", padx=20, pady=13,
                          relief="flat", bd=0, cursor="hand2", bg="#17243A",
                          fg="#D8E2F1", activebackground="#263957",
                          activeforeground="white", font=("Segoe UI", 10),
                          command=lambda k=key: self.show_page(k))
            b.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[key] = b

        tk.Frame(self.sidebar, bg="#34445E", height=1).pack(fill="x", padx=18, pady=18)
        tk.Label(self.sidebar, text="BASE DE DATOS", bg="#17243A", fg="#8FA2BF",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20)
        tk.Label(self.sidebar, text="Local • SQLite", bg="#17243A", fg="#D8E2F1",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(7, 0))
        tk.Button(self.sidebar, text="↻  Crear respaldo", anchor="w", padx=20, pady=10,
                  relief="flat", bd=0, cursor="hand2", bg="#17243A", fg="#D8E2F1",
                  activebackground="#263957", activeforeground="white",
                  font=("Segoe UI", 10), command=self.backup_db).pack(side="bottom", fill="x", padx=10, pady=14)

        self.main = tk.Frame(self, bg="#F3F6FB")
        self.main.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.main, bg="#FFFFFF", height=76)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        self.page_title = tk.Label(self.header, text="Panel principal", bg="white",
                                   fg="#172033", font=("Segoe UI", 19, "bold"))
        self.page_title.pack(side="left", padx=28)
        self.header_right = tk.Frame(self.header, bg="white")
        self.header_right.pack(side="right", padx=26)
        tk.Label(self.header_right, text="SISTEMA DE INVENTARIOS", bg="white",
                 fg="#73819A", font=("Segoe UI", 9, "bold")).pack(anchor="e")
        tk.Label(self.header_right, text=datetime.now().strftime("%d/%m/%Y"),
                 bg="white", fg="#172033", font=("Segoe UI", 10)).pack(anchor="e", pady=(3, 0))

        self.content = tk.Frame(self.main, bg="#F3F6FB")
        self.content.pack(fill="both", expand=True, padx=26, pady=22)
        self.pages = {}
        self.make_dashboard()
        self.make_products_page()
        self.make_movements_page()
        self.show_page("dashboard")

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.pack_forget()
            widget.grid_forget()

    def show_page(self, key):
        self.current_page = key
        titles = {"dashboard": "Panel principal", "products": "Catálogo de productos",
                  "movements": "Historial de movimientos"}
        self.page_title.configure(text=titles[key])
        for k, b in self.nav_buttons.items():
            b.configure(bg="#263957" if k == key else "#17243A",
                        fg="white" if k == key else "#D8E2F1")
        for k, frame in self.pages.items():
            frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        self.refresh_all()

    def card(self, parent, title, value, subtitle, accent):
        frame = tk.Frame(parent, bg="white", highlightbackground="#E2E8F2", highlightthickness=1)
        tk.Frame(frame, bg=accent, width=5).pack(side="left", fill="y")
        body = tk.Frame(frame, bg="white")
        body.pack(side="left", fill="both", expand=True, padx=16, pady=13)
        tk.Label(body, text=title.upper(), bg="white", fg="#7B879B",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        val = tk.Label(body, text=value, bg="white", fg="#172033",
                       font=("Segoe UI", 22, "bold"))
        val.pack(anchor="w", pady=(5, 2))
        tk.Label(body, text=subtitle, bg="white", fg="#7B879B",
                 font=("Segoe UI", 9)).pack(anchor="w")
        return frame, val

    def make_dashboard(self):
        page = tk.Frame(self.content, bg="#F3F6FB")
        self.pages["dashboard"] = page
        intro = tk.Frame(page, bg="#F3F6FB")
        intro.pack(fill="x", pady=(0, 18))
        tk.Label(intro, text="Resumen de operación", bg="#F3F6FB", fg="#172033",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(intro, text="Consulta el estado actual de tus existencias y movimientos.",
                 bg="#F3F6FB", fg="#73819A", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        cards = tk.Frame(page, bg="#F3F6FB")
        cards.pack(fill="x")
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1, uniform="cards")
        self.dashboard_cards = []
        specs = [
            ("Productos registrados", "0", "Referencias activas", "#3978E5"),
            ("Unidades en inventario", "0", "Existencia total", "#19A78A"),
            ("Valor a costo", "$0.00", "Costo estimado del stock", "#8B65D9"),
            ("Stock bajo", "0", "Requieren revisión", "#E59A32")
        ]
        for i, spec in enumerate(specs):
            card, value_label = self.card(cards, *spec)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            self.dashboard_cards.append(value_label)

        bottom = tk.Frame(page, bg="#F3F6FB")
        bottom.pack(fill="both", expand=True, pady=(22, 0))
        left = tk.Frame(bottom, bg="white", highlightbackground="#E2E8F2", highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(bottom, bg="white", width=310, highlightbackground="#E2E8F2", highlightthickness=1)
        right.pack(side="left", fill="y")
        right.pack_propagate(False)
        tk.Label(left, text="Productos con stock bajo", bg="white", fg="#172033",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(16, 12))
        self.low_tree = ttk.Treeview(left, columns=("sku", "name", "stock", "min"), show="headings", height=9)
        for col, title, width in [("sku", "SKU", 110), ("name", "Producto", 250),
                                  ("stock", "Existencia", 100), ("min", "Mínimo", 100)]:
            self.low_tree.heading(col, text=title)
            self.low_tree.column(col, width=width, anchor="w" if col in ("sku", "name") else "center")
        self.low_tree.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        tk.Label(right, text="Acciones rápidas", bg="white", fg="#172033",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=18, pady=(16, 14))
        self.action_button(right, "＋  Registrar producto", self.open_add_product, "#2563EB").pack(fill="x", padx=18, pady=5)
        self.action_button(right, "⇄  Registrar movimiento", self.open_movement, "#138A72").pack(fill="x", padx=18, pady=5)
        self.action_button(right, "⇩  Exportar productos CSV", self.export_products, "#52627A").pack(fill="x", padx=18, pady=5)
        tk.Label(right, text="Consejo", bg="white", fg="#172033",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(25, 5))
        tk.Label(right, text="Mantén actualizado el stock mínimo para detectar faltantes antes de que afecten las ventas.",
                 bg="white", fg="#73819A", justify="left", wraplength=255,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18)

    def action_button(self, parent, text, command, color):
        return tk.Button(parent, text=text, command=command, bg=color, fg="white",
                         activebackground=color, activeforeground="white", relief="flat",
                         bd=0, cursor="hand2", font=("Segoe UI", 10, "bold"), pady=11)

    def make_products_page(self):
        page = tk.Frame(self.content, bg="#F3F6FB")
        self.pages["products"] = page
        toolbar = tk.Frame(page, bg="#F3F6FB")
        toolbar.pack(fill="x", pady=(0, 14))
        self.product_search = tk.StringVar()
        search = ttk.Entry(toolbar, textvariable=self.product_search, width=36)
        search.pack(side="left", ipady=4)
        search.insert(0, "")
        search.bind("<KeyRelease>", lambda e: self.refresh_products())
        tk.Label(toolbar, text="Buscar por SKU, nombre, código o categoría",
                 bg="#F3F6FB", fg="#73819A", font=("Segoe UI", 9)).pack(side="left", padx=10)
        self.action_button(toolbar, "＋ Nuevo producto", self.open_add_product, "#2563EB").pack(side="right", padx=(8, 0))
        self.action_button(toolbar, "✎ Editar seleccionado", self.edit_selected_product, "#52627A").pack(side="right", padx=8)
        self.action_button(toolbar, "− Eliminar", self.delete_selected_product, "#C2414B").pack(side="right")
        tablebox = tk.Frame(page, bg="white", highlightbackground="#E2E8F2", highlightthickness=1)
        tablebox.pack(fill="both", expand=True)
        cols = ("id", "sku", "barcode", "name", "category", "stock", "min", "cost", "price", "location")
        self.products_tree = ttk.Treeview(tablebox, columns=cols, show="headings")
        headers = [("id", "ID", 45), ("sku", "SKU", 95), ("barcode", "Código barras", 115),
                   ("name", "Producto", 220), ("category", "Categoría", 120), ("stock", "Stock", 75),
                   ("min", "Mínimo", 75), ("cost", "Costo", 95), ("price", "Precio", 95),
                   ("location", "Ubicación", 100)]
        for col, title, width in headers:
            self.products_tree.heading(col, text=title)
            self.products_tree.column(col, width=width, anchor="w" if col in ("name", "category", "location") else "center")
        yscroll = ttk.Scrollbar(tablebox, orient="vertical", command=self.products_tree.yview)
        xscroll = ttk.Scrollbar(tablebox, orient="horizontal", command=self.products_tree.xview)
        self.products_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        tablebox.grid_rowconfigure(0, weight=1)
        tablebox.grid_columnconfigure(0, weight=1)
        self.products_tree.bind("<Double-1>", lambda e: self.edit_selected_product())
        footer = tk.Frame(page, bg="#F3F6FB")
        footer.pack(fill="x", pady=(10, 0))
        self.products_count = tk.Label(footer, text="0 productos", bg="#F3F6FB", fg="#73819A",
                                       font=("Segoe UI", 9))
        self.products_count.pack(side="left")
        self.action_button(footer, "⇩ Exportar CSV", self.export_products, "#52627A").pack(side="right")

    def make_movements_page(self):
        page = tk.Frame(self.content, bg="#F3F6FB")
        self.pages["movements"] = page
        toolbar = tk.Frame(page, bg="#F3F6FB")
        toolbar.pack(fill="x", pady=(0, 14))
        tk.Label(toolbar, text="Entradas, salidas y ajustes de existencias", bg="#F3F6FB",
                 fg="#73819A", font=("Segoe UI", 10)).pack(side="left")
        self.action_button(toolbar, "＋ Registrar movimiento", self.open_movement, "#138A72").pack(side="right")
        box = tk.Frame(page, bg="white", highlightbackground="#E2E8F2", highlightthickness=1)
        box.pack(fill="both", expand=True)
        cols = ("date", "sku", "name", "type", "qty", "before", "after", "note")
        self.movements_tree = ttk.Treeview(box, columns=cols, show="headings")
        headers = [("date", "Fecha y hora", 150), ("sku", "SKU", 95), ("name", "Producto", 220),
                   ("type", "Movimiento", 110), ("qty", "Cantidad", 85), ("before", "Stock anterior", 100),
                   ("after", "Stock nuevo", 100), ("note", "Nota", 230)]
        for col, title, width in headers:
            self.movements_tree.heading(col, text=title)
            self.movements_tree.column(col, width=width, anchor="w" if col in ("name", "note", "date") else "center")
        ys = ttk.Scrollbar(box, orient="vertical", command=self.movements_tree.yview)
        xs = ttk.Scrollbar(box, orient="horizontal", command=self.movements_tree.xview)
        self.movements_tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        self.movements_tree.grid(row=0, column=0, sticky="nsew")
        ys.grid(row=0, column=1, sticky="ns")
        xs.grid(row=1, column=0, sticky="ew")
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_products()
        self.refresh_movements()

    def refresh_dashboard(self):
        rows = self.conn.execute("SELECT * FROM products").fetchall()
        count = len(rows)
        units = sum(r["stock"] for r in rows)
        value = sum(r["stock"] * r["cost"] for r in rows)
        low = [r for r in rows if r["stock"] <= r["min_stock"]]
        if hasattr(self, "dashboard_cards"):
            vals = [str(count), f"{units:,}", money(value), str(len(low))]
            for label, value_text in zip(self.dashboard_cards, vals):
                label.configure(text=value_text)
        if hasattr(self, "low_tree"):
            for item in self.low_tree.get_children():
                self.low_tree.delete(item)
            for r in sorted(low, key=lambda x: x["stock"])[:100]:
                self.low_tree.insert("", "end", values=(r["sku"], r["name"], r["stock"], r["min_stock"]))

    def refresh_products(self):
        if not hasattr(self, "products_tree"):
            return
        query = self.product_search.get().strip() if hasattr(self, "product_search") else ""
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        if query:
            like = f"%{query}%"
            rows = self.conn.execute("""SELECT * FROM products
                WHERE sku LIKE ? OR barcode LIKE ? OR name LIKE ? OR category LIKE ? OR supplier LIKE ?
                ORDER BY name""", (like, like, like, like, like)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        for r in rows:
            self.products_tree.insert("", "end", iid=str(r["id"]), values=(
                r["id"], r["sku"], r["barcode"], r["name"], r["category"], r["stock"],
                r["min_stock"], money(r["cost"]), money(r["price"]), r["location"]))
        self.products_count.configure(text=f"{len(rows)} producto(s) mostrado(s)")

    def refresh_movements(self):
        if not hasattr(self, "movements_tree"):
            return
        for item in self.movements_tree.get_children():
            self.movements_tree.delete(item)
        rows = self.conn.execute("SELECT * FROM movements ORDER BY id DESC LIMIT 1000").fetchall()
        for r in rows:
            self.movements_tree.insert("", "end", values=(r["created_at"], r["sku"], r["product_name"],
                r["movement_type"], r["quantity"], r["previous_stock"], r["new_stock"], r["note"]))

    def open_add_product(self):
        self.product_dialog()

    def selected_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Selecciona un producto", "Selecciona un producto de la tabla.")
            return None
        return self.conn.execute("SELECT * FROM products WHERE id=?", (int(selected[0]),)).fetchone()

    def edit_selected_product(self):
        row = self.selected_product()
        if row:
            self.product_dialog(row)

    def product_dialog(self, row=None):
        editing = row is not None
        win = tk.Toplevel(self)
        win.title("Editar producto" if editing else "Nuevo producto")
        win.configure(bg="#F3F6FB")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        win.geometry("610x600")
        tk.Label(win, text="Editar producto" if editing else "Registrar producto",
                 bg="#F3F6FB", fg="#172033", font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=25, pady=(22, 4))
        tk.Label(win, text="Completa los datos del artículo. Los campos marcados con * son obligatorios.",
                 bg="#F3F6FB", fg="#73819A", font=("Segoe UI", 9)).pack(anchor="w", padx=25, pady=(0, 16))
        form = tk.Frame(win, bg="#F3F6FB")
        form.pack(fill="both", expand=True, padx=25)
        fields = [
            ("sku", "SKU / Clave *"), ("barcode", "Código de barras"),
            ("name", "Nombre del producto *"), ("category", "Categoría"),
            ("supplier", "Proveedor"), ("cost", "Costo unitario *"),
            ("price", "Precio de venta *"), ("stock", "Existencia inicial *"),
            ("min_stock", "Stock mínimo"), ("location", "Ubicación / pasillo")
        ]
        entries = {}
        for i, (key, label) in enumerate(fields):
            r, c = divmod(i, 2)
            cell = tk.Frame(form, bg="#F3F6FB")
            cell.grid(row=r, column=c, sticky="ew", padx=(0 if c == 0 else 12, 0), pady=7)
            tk.Label(cell, text=label, bg="#F3F6FB", fg="#34415A",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))
            ent = ttk.Entry(cell, width=30)
            ent.pack(fill="x", ipady=3)
            entries[key] = ent
            form.grid_columnconfigure(c, weight=1)
            if editing:
                ent.insert(0, str(row[key] if row[key] is not None else ""))
        if editing:
            entries["stock"].configure(state="disabled")
            entries["stock"].delete(0, "end")
            entries["stock"].insert(0, str(row["stock"]))
            tk.Label(form, text="Para cambiar existencias usa 'Registrar movimiento'.",
                     bg="#F3F6FB", fg="#B56A13", font=("Segoe UI", 9)).grid(row=5, column=0, columnspan=2, sticky="w", pady=(2, 0))
        buttons = tk.Frame(win, bg="#F3F6FB")
        buttons.pack(fill="x", padx=25, pady=22)

        def save():
            data = {k: e.get().strip() for k, e in entries.items()}
            if not data["sku"] or not data["name"]:
                messagebox.showerror("Datos incompletos", "SKU y nombre del producto son obligatorios.", parent=win)
                return
            try:
                cost = float(data["cost"] or 0)
                price = float(data["price"] or 0)
                stock = int(row["stock"] if editing else (data["stock"] or 0))
                min_stock = int(data["min_stock"] or 0)
                if cost < 0 or price < 0 or stock < 0 or min_stock < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Datos inválidos", "Costo, precio y existencias deben ser números válidos no negativos.", parent=win)
                return
            try:
                with self.conn:
                    if editing:
                        self.conn.execute("""UPDATE products SET sku=?, barcode=?, name=?, category=?, supplier=?,
                            cost=?, price=?, min_stock=?, location=? WHERE id=?""",
                            (data["sku"], data["barcode"], data["name"], data["category"], data["supplier"],
                             cost, price, min_stock, data["location"], row["id"]))
                    else:
                        self.conn.execute("""INSERT INTO products
                            (sku, barcode, name, category, supplier, cost, price, stock, min_stock, location, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (data["sku"], data["barcode"], data["name"], data["category"], data["supplier"],
                             cost, price, stock, min_stock, data["location"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        pid = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                        if stock:
                            self.conn.execute("""INSERT INTO movements
                                (product_id, sku, product_name, movement_type, quantity, previous_stock, new_stock, note, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (pid, data["sku"], data["name"], "Stock inicial", stock, 0, stock,
                                 "Existencia al registrar producto", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                win.destroy()
                self.refresh_all()
            except sqlite3.IntegrityError:
                messagebox.showerror("SKU duplicado", "Ya existe un producto con ese SKU. Usa una clave diferente.", parent=win)
            except sqlite3.Error as ex:
                messagebox.showerror("Error de base de datos", str(ex), parent=win)

        self.action_button(buttons, "Cancelar", win.destroy, "#64748B").pack(side="right", padx=(8, 0))
        self.action_button(buttons, "Guardar producto", save, "#2563EB").pack(side="right")

    def delete_selected_product(self):
        row = self.selected_product()
        if not row:
            return
        if not messagebox.askyesno("Confirmar eliminación",
                f"¿Eliminar '{row['name']}'? Se conservará el historial de movimientos, pero ya no podrás ver el producto en el catálogo."):
            return
        # Preserve historical records by preventing deletion when movements exist.
        has_moves = self.conn.execute("SELECT COUNT(*) FROM movements WHERE product_id=?", (row["id"],)).fetchone()[0]
        if has_moves:
            messagebox.showwarning("Producto con historial",
                "Este producto tiene movimientos registrados. No se puede eliminar para proteger la trazabilidad. Puedes editarlo o dejarlo con stock cero.")
            return
        with self.conn:
            self.conn.execute("DELETE FROM products WHERE id=?", (row["id"],))
        self.refresh_all()

    def open_movement(self):
        products = self.conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        if not products:
            messagebox.showinfo("Sin productos", "Primero registra al menos un producto.")
            self.show_page("products")
            return
        win = tk.Toplevel(self)
        win.title("Registrar movimiento de inventario")
        win.geometry("520x470")
        win.resizable(False, False)
        win.configure(bg="#F3F6FB")
        win.transient(self)
        win.grab_set()
        tk.Label(win, text="Movimiento de inventario", bg="#F3F6FB", fg="#172033",
                 font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=25, pady=(22, 4))
        tk.Label(win, text="Registra entradas, salidas o ajustes con trazabilidad.",
                 bg="#F3F6FB", fg="#73819A", font=("Segoe UI", 9)).pack(anchor="w", padx=25, pady=(0, 18))
        form = tk.Frame(win, bg="#F3F6FB")
        form.pack(fill="x", padx=25)
        tk.Label(form, text="Producto", bg="#F3F6FB", fg="#34415A").pack(anchor="w")
        product_map = {f"{p['sku']} — {p['name']} (stock: {p['stock']})": p for p in products}
        product_var = tk.StringVar(value=next(iter(product_map)))
        combo = ttk.Combobox(form, textvariable=product_var, values=list(product_map), state="readonly")
        combo.pack(fill="x", pady=(4, 13), ipady=3)
        tk.Label(form, text="Tipo de movimiento", bg="#F3F6FB", fg="#34415A").pack(anchor="w")
        type_var = tk.StringVar(value="Entrada")
        type_combo = ttk.Combobox(form, textvariable=type_var, values=["Entrada", "Salida", "Ajuste"], state="readonly")
        type_combo.pack(fill="x", pady=(4, 13), ipady=3)
        tk.Label(form, text="Cantidad", bg="#F3F6FB", fg="#34415A").pack(anchor="w")
        qty_entry = ttk.Entry(form)
        qty_entry.pack(fill="x", pady=(4, 13), ipady=3)
        tk.Label(form, text="Nota / motivo", bg="#F3F6FB", fg="#34415A").pack(anchor="w")
        note_entry = ttk.Entry(form)
        note_entry.pack(fill="x", pady=(4, 13), ipady=3)
        tk.Label(form, text="En un ajuste, la cantidad representa el stock final deseado.",
                 bg="#F3F6FB", fg="#73819A", font=("Segoe UI", 9)).pack(anchor="w")
        buttons = tk.Frame(win, bg="#F3F6FB")
        buttons.pack(fill="x", padx=25, pady=22)

        def save_move():
            product = product_map.get(product_var.get())
            try:
                qty = int(qty_entry.get().strip())
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Cantidad inválida", "Introduce un entero mayor que cero.", parent=win)
                return
            kind = type_var.get()
            old = int(product["stock"])
            if kind == "Entrada":
                new = old + qty
            elif kind == "Salida":
                if qty > old:
                    messagebox.showerror("Stock insuficiente", f"Solo hay {old} unidades disponibles.", parent=win)
                    return
                new = old - qty
            else:
                new = qty
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with self.conn:
                    self.conn.execute("UPDATE products SET stock=? WHERE id=?", (new, product["id"]))
                    self.conn.execute("""INSERT INTO movements
                        (product_id, sku, product_name, movement_type, quantity, previous_stock, new_stock, note, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (product["id"], product["sku"], product["name"], kind, qty, old, new, note_entry.get().strip(), now))
                win.destroy()
                self.refresh_all()
            except sqlite3.Error as ex:
                messagebox.showerror("Error", str(ex), parent=win)

        self.action_button(buttons, "Cancelar", win.destroy, "#64748B").pack(side="right", padx=(8, 0))
        self.action_button(buttons, "Guardar movimiento", save_move, "#138A72").pack(side="right")

    def export_products(self):
        path = filedialog.asksaveasfilename(title="Exportar inventario", defaultextension=".csv",
                    filetypes=[("Archivo CSV", "*.csv")], initialfile=f"inventario_{datetime.now():%Y%m%d}.csv")
        if not path:
            return
        rows = self.conn.execute("SELECT sku, barcode, name, category, supplier, cost, price, stock, min_stock, location FROM products ORDER BY name").fetchall()
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["SKU", "Código de barras", "Producto", "Categoría", "Proveedor",
                                 "Costo", "Precio venta", "Stock", "Stock mínimo", "Ubicación"])
                for r in rows:
                    writer.writerow(list(r))
            messagebox.showinfo("Exportación completada", f"Se exportaron {len(rows)} productos a:\n{path}")
        except OSError as ex:
            messagebox.showerror("Error de exportación", str(ex))

    def backup_db(self):
        path = filedialog.asksaveasfilename(title="Guardar respaldo de base de datos",
                defaultextension=".db", filetypes=[("Base de datos SQLite", "*.db")],
                initialfile=f"respaldo_inventario_{datetime.now():%Y%m%d_%H%M}.db")
        if not path:
            return
        try:
            dest = sqlite3.connect(path)
            with dest:
                self.conn.backup(dest)
            dest.close()
            messagebox.showinfo("Respaldo creado", f"Respaldo guardado en:\n{path}")
        except (sqlite3.Error, OSError) as ex:
            messagebox.showerror("Error de respaldo", str(ex))

    def on_close(self):
        try:
            self.conn.close()
        finally:
            self.destroy()

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
