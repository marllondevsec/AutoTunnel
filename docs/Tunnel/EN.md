# Adding New Tunnel Providers

This document explains, in detail, how to create and integrate new tunnel providers into **AutoTunnel** using the built‑in plugin system.

The goal of the architecture is to make tunnel providers **isolated, portable, auto‑discoverable, and safe to extend** without modifying the core application.

---

## 🧠 Architecture Overview

AutoTunnel uses a **plugin-based tunnel system**.

* Each tunnel provider lives in its own Python file
* Providers are dynamically discovered at runtime
* The core application never hardcodes provider logic
* All providers follow the same minimal interface

This allows:

* Easy extension
* Clean separation of concerns
* Independent maintenance per provider

---

## 📁 Directory Structure

All tunnel providers must live inside the `tunnels/` directory:

```
AutoTunnel/
├── AutoTunnel.py
├── tunnels/
│   ├── Cloudflared.py
│   ├── Ngrok.py
│   └── YourTunnel.py   ← new provider
```

The filename **does not matter**, but it must end with `.py`.

---

## 🔍 Provider Auto‑Discovery

At startup, AutoTunnel:

1. Scans the `tunnels/` directory
2. Imports every `.py` file
3. Searches for a class named `TunnelPlugin`
4. Instantiates the class
5. Registers it internally

If any of these steps fail, the provider is silently skipped to avoid breaking the application.

---

## 🧩 Required Class: `TunnelPlugin`

Every provider **must** expose a class named:

```
TunnelPlugin
```

This class is the contract between the provider and AutoTunnel.

---

## ✅ Mandatory Methods

Your `TunnelPlugin` class **must** implement the following methods.

### `name(self) -> str`

Returns the display name of the tunnel provider.

Used for:

* Menu listing
* Logs
* State tracking

Example:

```
def name(self):
    return "MyTunnel"
```

---

### `installed(self) -> bool`

Checks whether the tunnel binary is already available on the system.

Responsibilities:

* Verify binary existence
* Return `True` if usable
* Return `False` if installation is required

Example:

```
def installed(self):
    return os.path.exists(self.binary_path)
```

---

### `install(self) -> None`

Handles provider installation.

Guidelines:

* Must be **fully automatic**
* Must not require user interaction
* Must install in AutoTunnel portable directories
* Should raise exceptions on failure

Typical tasks:

* Download binary
* Set executable permissions
* Validate installation

---

### `start(self, port: int) -> str`

Starts the tunnel and exposes a local port.

Parameters:

* `port`: local HTTP server port

Responsibilities:

* Spawn the tunnel process
* Capture stdout/stderr if needed
* Extract the public URL
* Store process PID

Must return:

* The public tunnel URL as a string

Example:

```
def start(self, port):
    self.process = subprocess.Popen([...])
    return public_url
```

---

### `stop(self) -> None`

Stops the running tunnel instance.

Responsibilities:

* Terminate the tunnel process
* Cleanup temporary files if needed
* Fail gracefully if already stopped

Example:

```
def stop(self):
    if self.process:
        self.process.terminate()
```

---

## 📦 Optional Methods

### `description(self) -> str`

Returns a short human‑readable description of the provider.

Used in menus and documentation panels.

---

### `requires_auth(self) -> bool`

Indicates whether the provider requires authentication (API token, account, etc).

If `True`, AutoTunnel will automatically:

* Ask the user for credentials
* Store them securely in config

---

### `configure(self, config: dict) -> None`

Allows custom configuration logic for advanced providers.

Useful for:

* Tokens
* Regions
* Custom domains

---

## 🔐 Configuration & Storage

Providers must **never** hardcode paths.

Use AutoTunnel’s portable directories:

* Config: `~/.config/autotunnel/`
* Data: `~/.local/share/autotunnel/`

All provider-specific data should live inside a subdirectory:

```
~/.local/share/autotunnel/mytunnel/
```

---

## 📝 Logging Rules

Providers should:

* Log important events (start, stop, errors)
* Avoid excessive verbosity
* Never print secrets or tokens

Logs are automatically captured by AutoTunnel when possible.

---

## ❌ What NOT To Do

* Do NOT modify `AutoTunnel.py`
* Do NOT hardcode absolute paths
* Do NOT block execution with `input()`
* Do NOT require manual installation steps
* Do NOT crash on errors — fail gracefully

---

## 🧪 Testing Your Provider

Before submitting or using a provider:

1. Remove existing binaries
2. Start AutoTunnel
3. Select your provider
4. Verify auto-install
5. Start a tunnel
6. Stop the tunnel
7. Restart AutoTunnel and test again

Your provider should survive restarts cleanly.

---

## 📌 Example Providers

Use the built-in providers as reference implementations:

* `tunnels/Cloudflared.py`
* `tunnels/Ngrok.py`

They demonstrate:

* Binary installation
* Process handling
* URL extraction
* Error handling

---

## 🚀 Contribution Guidelines

When contributing a new provider:

* Follow this document strictly
* Keep code readable and minimal
* Add comments where behavior is non-obvious
* Test on a clean system

