# MCP RunCmd

Servidor **MCP (Model Context Protocol)** para **LM Studio** que permite ejecutar comandos del sistema y scripts de Python de forma controlada.  

Este servidor expone varias herramientas como:
- `run_cmd` → Ejecutar comandos en shell.
- `list_dir` → Listar directorios.
- `read_text` → Leer archivos de texto.
- `write_text` → Escribir archivos de texto.
- `run_python_file` → Ejecutar scripts Python existentes.
- `run_python` → Ejecutar código Python inline.

---

## 🚀 Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/TU_USUARIO/mcp-run-cmd.git
   cd mcp-run-cmd
   ```

2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Uso

Ejecuta el servidor:

```bash
python runCmd.py
```

---

## ⚙️ Integración con LM Studio

En tu archivo `mcp.json` de configuración de LM Studio, añade una entrada como esta:

```json
{
  "name": "MCP RunCmd",
  "description": "Servidor MCP para ejecutar comandos y scripts desde LM Studio",
  "binary": "python",
  "args": ["runCmd.py"],
  "env": {},
  "autoStart": true
}
```

Guarda este archivo junto a `runCmd.py` y LM Studio detectará el servidor automáticamente.

---

## 📂 Archivos principales

- `runCmd.py` → Servidor MCP con las herramientas.
- `requirements.txt` → Dependencias necesarias.
- `README.md` → Documentación básica del proyecto.
- `mcp.json` → Configuración de ejemplo para LM Studio.

---

## 📜 Licencia
MIT
