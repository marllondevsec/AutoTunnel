# AutoTunnel

![AutoTunnel Main Menu](docs/examples/pic.png)

AutoTunnel is a portable, interactive CLI tool that spins up local HTTP servers and exposes them to the internet using secure tunnels such as **Cloudflare Tunnel (cloudflared)** and **ngrok**. It was designed to be fast, self-contained, and easy to use, with zero hard-coded paths and full portability across systems.

Ideal for labs, development, demos, internal sharing, and controlled security testing environments.

---

## ✨ Features

* 🚀 Start local HTTP servers instantly
* 🌐 Expose local services via Cloudflare Tunnel or ngrok
* 🔌 Plugin-based tunnel architecture
* 🧭 Interactive numeric menus (no flags needed)
* 🎨 Colored UI powered by `rich`
* 📦 Automatic tunnel binary installation (portable)
* 🗂️ Fully portable paths (XDG / `~/.config`, `~/.local/share`)
* 📝 Persistent logs, PIDs, and session metadata
* 🌍 Multi-language support (PT / EN)
* 📋 Automatic URL copy to clipboard

---

## 📂 Project Structure

```
AutoTunnel/
├── AutoTunnel.py          # Main application (CLI + server manager)
├── tunnels/
│   ├── Cloudflared.py     # Cloudflare Tunnel plugin
│   └── Ngrok.py           # Ngrok plugin
├── lang/
│   ├── pt.json            # Portuguese translations
│   └── en.json            # English translations
├── docs/
│   └── examples/
│       └── pic.png        # Main menu screenshot
└── README.md
```

Runtime data is stored in portable locations:

* **Config:** `~/.config/autotunnel/`
* **Data / Logs / PIDs:** `~/.local/share/autotunnel/`

---

## 🛠 Requirements

* Python **3.8+**
* Linux (tested primarily on Kali / Debian-based systems)
* Internet access (for tunnel installation)

Optional (installed automatically if missing):

* `rich`
* `cloudflared`
* `ngrok`

---

## ▶️ Usage

Make the script executable and run:

```bash
chmod +x AutoTunnel.py
./AutoTunnel.py
```

You will be presented with an interactive menu to:

* Start / stop HTTP servers
* Start tunnels with or without servers
* View active services
* Inspect logs
* Manage settings (language, ports, directories, tokens)

No command-line arguments required.

---

## 🌐 Supported Tunnels

### Cloudflare Tunnel (cloudflared)

* No account required
* Uses `trycloudflare.com`
* Installed automatically in portable mode

### Ngrok

* Requires an authentication token
* Token is requested once and stored securely in config
* Installed automatically in portable mode

---

## 🔌 Plugin System

Each tunnel provider is implemented as a self-contained plugin.

To add a new tunnel provider:

1. Create a new Python file in `tunnels/`
2. Implement a `TunnelPlugin` class
3. Define at minimum:

   * `name()`
   * `installed()`
   * `start(port)`
   * `stop()`

The plugin will be auto-discovered at runtime.

---

## 📝 Logs & State

AutoTunnel automatically tracks:

* Active servers and tunnels
* PIDs and ports
* Public URLs
* Start time

Logs are stored per-service and can be viewed live from the UI.

---

## 🔐 Security Notes

* Designed for **controlled environments** (labs, dev, demos)
* Exposes local services to the public internet — use responsibly
* No authentication or access control is added by default

---

## 📌 Version

**AutoTunnel v1.5**

---

## 👨‍💻 Author

**Marllon DevSec**

* GitHub: [https://github.com/marllondevsec](https://github.com/marllondevsec)
* LinkedIn: [https://www.linkedin.com/in/marllondevsec/](https://www.linkedin.com/in/marllondevsec/)

---

## 📄 License

This project is provided for educational and development purposes.

Use responsibly.
