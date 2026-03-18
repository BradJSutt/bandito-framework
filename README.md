<p align="center">
  <img src="https://img.shields.io/badge/Bandito-v1.0-red?style=for-the-badge&logo=python&logoColor=white" alt="Bandito v1.0">
  <img src="https://img.shields.io/badge/Purpose-Educational-blue?style=for-the-badge" alt="Educational">
  <img src="https://img.shields.io/badge/Target-DVWA%20%7C%20BoF-orange?style=for-the-badge" alt="DVWA + BoF">
  <img src="https://img.shields.io/badge/Python-3.10%2B-yellow?style=for-the-badge&logo=python" alt="Python 3.10+">
</p>

<h1 align="center">Bandito Framework</h1>

<p align="center">
  <strong>A modular, Metasploit-inspired exploitation framework for DVWA and buffer overflow research.</strong><br>
  Built for Assignment 3 — covering Command Injection, File Upload, Reflected XSS, Stored XSS, SQL Injection, and Buffer Overflow.
</p>

<p align="center">
  <em>For educational and authorised testing only. Do not use against systems you do not own.</em>
</p>

---

## Features

- Metasploit-style CLI (`use`, `set`, `run`, `show options`, `browse`)
- Automatic DVWA login and CSRF token handling (shared `DVWABase` class)
- Interactive command shell via command injection
- PHP webshell and reverse shell upload with auto-listener
- Reflected and Stored XSS payload generation with clipboard copy
- SQL injection dump + hashcat hash cracking
- Guided buffer overflow analysis (fuzz → pattern → offset → badchars → EIP control)
- Automated BoF exploit with msfvenom payload generation
- cmatrix loading animation and full ANSI colour output

---

## Project Structure

```
bandito-framework/
├── bandito.py                   ← Framework entry point
├── base_module.py               ← BaseModule (all modules inherit this)
├── dvwa_base.py                 ← DVWABase (shared login/CSRF — DVWA modules inherit this)
├── utils.py                     ← Colour output, banner, cmatrix animation
├── requirements.txt
├── README.md
└── modules/
    ├── buffer_overflow/
    │   ├── benjis_snack_vault_analysis.py   ← Guided BoF analysis
    │   └── benjis_snack_vault_bo.py         ← Automated BoF exploit
    ├── command_injection/
    │   └── rce.py                           ← Command injection → RCE
    ├── sqli/
    │   └── sqli.py                          ← SQL injection + hash cracking
    └── xss/
        ├── xss.py                           ← Reflected XSS
        └── xss_stored.py                    ← Stored XSS cookie stealer
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/BradJSutt/banditoProject.git
cd banditoProject

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Launch
python3 bandito.py
```

> **Requirements:** Python 3.10+, Kali Linux (or any Linux with Metasploit installed for BoF modules)

---

## Module Workflows

### Command Injection → RCE
```
use command_injection.rce
set RHOST <dvwa_ip>
set LHOST <your_kali_ip>
run
upload_webshell        # drops shell.php
upload_revshell        # drops rev.php + opens nc listener automatically
shell                  # interactive command shell via injection
```

### Reflected XSS
```
use xss.xss_reflected
set RHOST <dvwa_ip>
setup                  # starts HTTP catch server + opens DVWA page
generate               # prints payload to paste into the XSS form
```

### Stored XSS (Cookie Stealer)
```
use xss.xss_stored
set RHOST <dvwa_ip>
setup                  # starts HTTP catch server + opens Stored XSS page
generate               # prints guestbook payload
```
> Tip: right-click the Message field → Inspect → increase `maxlength` before pasting.

### SQL Injection + Hash Cracking
```
use sqli.sqli
set RHOST <dvwa_ip>
run                    # login → dump hashes → crack with hashcat
```

### Buffer Overflow (Analysis)
```
use buffer_overflow.benjis_snack_vault_analysis
set RHOST <target_ip>
run                    # full guided chain (fuzz → pattern → offset → badchars → EIP test)
```
Results are saved to `analysis_results.json` and auto-loaded by the exploit module.

### Buffer Overflow (Exploit)
```
use buffer_overflow.benjis_snack_vault_bo
set LHOST <your_kali_ip>
run                    # generates Meterpreter payload + fires exploit
```

---

## Adding a New Module

1. Create a `.py` file anywhere under `modules/`.
2. Subclass `BaseModule` (or `DVWABase` for DVWA targets).
3. Set `self.name`, `self.description`, and `self.options`.
4. Implement `run()` and optionally override `show_help()` / `handle_command()`.
5. Restart Bandito — your module is loaded automatically.

```python
from base_module import BaseModule
from utils import colored

class MyModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name        = "my_module"
        self.description = "Does something cool"
        self.options = {
            "TARGET": {"value": "", "required": True, "description": "Target IP"},
        }

    def run(self):
        print(colored(f"Running against {self.options['TARGET']['value']}", "green"))
```

---

## Author

**Brad Sutton** — Cybersecurity student and researcher.  
Built as a portfolio project demonstrating modular exploit framework design, DVWA attack chains, and Python tooling.
