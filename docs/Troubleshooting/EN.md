# Troubleshooting & Reset Guide

This document explains how to resolve common startup and runtime issues in **AutoTunnel**, especially cases where the application fails to initialize due to corrupted state or configuration files.

Before opening an issue or requesting a fix, **please follow the steps below**.

---

## 🚨 Common Issue: AutoTunnel Does Not Start

In some situations, AutoTunnel may fail to start correctly. This usually happens due to:

* Corrupted state files
* Invalid or partially written JSON files
* Interrupted shutdowns (forced close, system crash)
* Stale PID or process metadata

These issues can prevent AutoTunnel from loading its internal state.

---

## 🧠 Why This Happens

AutoTunnel stores runtime state and configuration data in portable directories:

* Active processes
* Running tunnels
* Server metadata
* User configuration

If one of these files becomes corrupted, the application may not initialize properly.

The good news: **this can be safely fixed without reinstalling AutoTunnel**.

---

## 🧹 Safe Reset Procedure (Recommended)

The following steps will reset AutoTunnel’s state **without removing tunnel binaries**.

### 1️⃣ Remove Corrupted State Files

Run the commands below:

```bash
# Remove corrupted runtime state (keeps tunnel binaries)
rm -f ~/.local/share/autotunnel/active_processes.json
rm -rf ~/.local/share/autotunnel/pids/*.json
rm -f ~/.config/autotunnel/config.json
```

What this does:

* Removes active process tracking
* Clears stale PID references
* Resets configuration to default
* Keeps all downloaded tunnel binaries intact

---

### 2️⃣ Restart AutoTunnel

After cleanup, start AutoTunnel again:

```bash
python3 AutoTunnel.py
```

On startup, AutoTunnel will:

* Recreate missing configuration files
* Regenerate internal state safely
* Start normally

---

## ✅ When to Use This Reset

Use this procedure if:

* AutoTunnel crashes on startup
* The menu does not load
* Services appear active but cannot be stopped
* Tunnels fail to start with no clear error

This should always be your **first troubleshooting step**.

---

## ❌ When NOT to Open an Issue Yet

Please do **not** open a GitHub issue if the problem is resolved after performing the reset above.

This helps keep the issue tracker clean and focused on real bugs.

---

## 🐞 When to Open an Issue

If the problem **persists after the reset**, please open an issue and include:

* Your operating system
* Python version
* Error messages or stack traces
* Steps to reproduce the issue

This will greatly speed up debugging and fixes.

---

## 🛡️ Data Safety Note

This reset does **not**:

* Remove tunnel binaries
* Remove downloaded providers
* Affect system-wide configuration

It only clears AutoTunnel’s internal state.

---

## 📌 Final Recommendation

Always try this reset procedure **before requesting support**.

It solves the vast majority of startup-related issues.

---

Happy tunneling 🚀
