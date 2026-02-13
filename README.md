<p align="center">
  <img src="https://img.shields.io/badge/Bandito-v1.0-red?style=for-the-badge&logo=python&logoColor=white" alt="Bandito v1.0">
  <img src="https://img.shields.io/badge/Purpose-Educational-blue?style=for-the-badge" alt="Educational">
  <img src="https://img.shields.io/badge/Target-DVWA-orange?style=for-the-badge" alt="DVWA">
</p>

<h1 align="center">
  Bandito Framework
</h1>

<p align="center">
  <strong>A clean, modular exploitation framework for DVWA</strong><br>
  Designed for Assignment 3 – covering Command Injection, File Upload, Reflected XSS, Stored XSS, and SQL Injection.
</p>

<p align="center">
  <em>For educational and authorized testing only. Do not use against production systems.</em>
</p>

<br>

## 🔥 Quick Features

- Metasploit-inspired CLI (options, set, run)
- Automatic login & CSRF handling
- Interactive shell via command injection
- Webshell + reverse shell with auto-listener
- Reflected & Stored XSS payload generation
- SQL injection dump + hashcat cracking
- Beautiful cmatrix loading + colored output

## 🚀 Quick Start

1. Clone the repo

   ```bash
   git clone https://github.com/BradJSutt/banditoProject.git
   cd banditoProject

2. pip3 install -r requirements.txt

3. run the framework inside of the folder using:
   python3 bandito.py

## Fastest commands to test all modules:

use rce
set LHOST <your_kali_ip>
run
upload_webshell
upload_revshell
back

use xss
setup
generate_reflected
paste in DVWA reflected page

use stored_xss
setup
generate_stored
paste in DVWA guestbook

use sqli
run
check dvwa_hashes.txt + hashcat output