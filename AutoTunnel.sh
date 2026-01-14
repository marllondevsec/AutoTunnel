#!/bin/bash
# =============================================================================
# TUNNEL MANAGER - Versão Simplificada e Corrigida
# =============================================================================

# Verificar versão do Bash
if ((BASH_VERSINFO[0] < 4)); then
    echo "Este script requer bash 4+. Versão atual: $BASH_VERSION" >&2
    exit 1
fi

# Configurações básicas
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="2.1.0"
CONFIG_FILE="$HOME/.tunnel-manager.conf"
LOG_DIR="$HOME/.tunnel-manager/logs"
PID_FILE="/tmp/tunnel-manager.pid"
DEFAULT_PORT=1337
DEFAULT_DIR="$SCRIPT_DIR/www"
CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"

# Idioma
LANGUAGE="pt"
declare -A TEXT

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'

# =============================================================================
# SISTEMA DE IDIOMAS SIMPLIFICADO
# =============================================================================

load_language() {
    local lang=$1
    TEXT=()  # Limpar array
    
    if [[ "$lang" == "en" ]]; then
        TEXT[menu_title]="TUNNEL MANAGER v$VERSION"
        TEXT[menu_options]="MENU OPTIONS"
        TEXT[menu_1]="Start new tunnel"
        TEXT[menu_2]="Start tunnel in current directory"
        TEXT[menu_3]="View active tunnels"
        TEXT[menu_4]="View logs"
        TEXT[menu_5]="Stop all tunnels"
        TEXT[menu_6]="Install Cloudflared (system)"
        TEXT[menu_7]="Settings"
        TEXT[menu_8]="About"
        TEXT[menu_9]="Change language"
        TEXT[menu_0]="Exit"
        TEXT[menu_choose]="Choose an option: "
        TEXT[press_any_key]="Press any key to continue..."
        TEXT[invalid_option]="Invalid option"
        TEXT[success]="Success"
        TEXT[error]="Error"
        TEXT[warning]="Warning"
        TEXT[enter_port]="Enter HTTP server port (default: $DEFAULT_PORT): "
        TEXT[port_in_use]="Port {1} is already in use"
        TEXT[stop_port]="Stop process on port {1}? (y/N): "
        TEXT[dir_selection]="HTTP server directory:"
        TEXT[dir_option1]="1) Use current directory ($(pwd))"
        TEXT[dir_option2]="2) Use default directory ($DEFAULT_DIR)"
        TEXT[dir_option3]="3) Specify another directory"
        TEXT[choose_dir]="Choose (1-3, default: 1): "
        TEXT[enter_dir]="Enter directory path: "
        TEXT[using_current]="Using current directory: {1}"
        TEXT[using_default]="Using default directory: {1}"
        TEXT[using_custom]="Using directory: {1}"
        TEXT[starting_http]="Starting HTTP Server on port {1}..."
        TEXT[http_started]="HTTP Server started (PID: {1})"
        TEXT[tunnel_created]="✅ TUNNEL CREATED SUCCESSFULLY!"
        TEXT[tunnel_url]="URL: {1}"
        TEXT[local_url]="Local: http://localhost:{2}"
        TEXT[server_dir]="Directory: {3}"
        TEXT[checking_deps]="Checking dependencies..."
        TEXT[python_found]="Python3 found"
        TEXT[cloudflared_found]="Cloudflared found"
        TEXT[cloudflared_not_found]="Cloudflared not found"
        TEXT[downloading_cf]="Downloading Cloudflared..."
    else
        # Português (padrão)
        TEXT[menu_title]="TUNNEL MANAGER v$VERSION"
        TEXT[menu_options]="MENU DE OPÇÕES"
        TEXT[menu_1]="Iniciar novo túnel"
        TEXT[menu_2]="Iniciar túnel no diretório atual"
        TEXT[menu_3]="Ver túneis ativos"
        TEXT[menu_4]="Ver logs"
        TEXT[menu_5]="Parar todos os túneis"
        TEXT[menu_6]="Instalar Cloudflared (sistema)"
        TEXT[menu_7]="Configurações"
        TEXT[menu_8]="Sobre"
        TEXT[menu_9]="Mudar idioma"
        TEXT[menu_0]="Sair"
        TEXT[menu_choose]="Escolha uma opção: "
        TEXT[press_any_key]="Pressione qualquer tecla para continuar..."
        TEXT[invalid_option]="Opção inválida"
        TEXT[success]="Sucesso"
        TEXT[error]="Erro"
        TEXT[warning]="Aviso"
        TEXT[enter_port]="Porta para o servidor HTTP (padrão: $DEFAULT_PORT): "
        TEXT[port_in_use]="Porta {1} já está em uso"
        TEXT[stop_port]="Parar processo na porta {1}? (s/N): "
        TEXT[dir_selection]="Diretório do servidor HTTP:"
        TEXT[dir_option1]="1) Usar diretório atual ($(pwd))"
        TEXT[dir_option2]="2) Usar diretório padrão ($DEFAULT_DIR)"
        TEXT[dir_option3]="3) Especificar outro diretório"
        TEXT[choose_dir]="Escolha (1-3, padrão: 1): "
        TEXT[enter_dir]="Digite o caminho do diretório: "
        TEXT[using_current]="Usando diretório atual: {1}"
        TEXT[using_default]="Usando diretório padrão: {1}"
        TEXT[using_custom]="Usando diretório: {1}"
        TEXT[starting_http]="Iniciando HTTP Server na porta {1}..."
        TEXT[http_started]="HTTP Server iniciado (PID: {1})"
        TEXT[tunnel_created]="✅ TÚNEL CRIADO COM SUCESSO!"
        TEXT[tunnel_url]="URL: {1}"
        TEXT[local_url]="Local: http://localhost:{2}"
        TEXT[server_dir]="Diretório: {3}"
        TEXT[checking_deps]="Verificando dependências..."
        TEXT[python_found]="Python3 encontrado"
        TEXT[cloudflared_found]="Cloudflared encontrado"
        TEXT[cloudflared_not_found]="Cloudflared não encontrado"
        TEXT[downloading_cf]="Baixando Cloudflared..."
    fi
}

# Função get_text corrigida
get_text() {
    local key="$1"
    local text="${TEXT[$key]}"
    
    if [ -z "$text" ]; then
        echo "[Texto não encontrado: $key]"
        return
    fi
    
    shift
    local i=1
    for arg in "$@"; do
        text="${text//\{$i\}/$arg}"
        ((i++))
    done
    
    echo "$text"
}

# =============================================================================
# FUNÇÕES PRINCIPAIS
# =============================================================================

print_banner() {
    clear
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text menu_title)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
}

show_menu() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text menu_options)${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}1)${NC} $(get_text menu_1)"
    echo -e "${GREEN}2)${NC} $(get_text menu_2)"
    echo -e "${GREEN}3)${NC} $(get_text menu_3)"
    echo -e "${GREEN}4)${NC} $(get_text menu_4)"
    echo -e "${GREEN}5)${NC} $(get_text menu_5)"
    echo -e "${GREEN}6)${NC} $(get_text menu_6)"
    echo -e "${GREEN}7)${NC} $(get_text menu_7)"
    echo -e "${GREEN}8)${NC} $(get_text menu_8)"
    echo -e "${GREEN}9)${NC} $(get_text menu_9)"
    echo -e "${GREEN}0)${NC} $(get_text menu_0)"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$(get_text menu_choose)${NC}"
    
    read -r option
    
    case $option in
        1) start_tunnel ;;
        2) start_current_dir_tunnel ;;
        3) echo -e "\n${YELLOW}Função em desenvolvimento...${NC}"; sleep 1; show_menu ;;
        4) echo -e "\n${YELLOW}Função em desenvolvimento...${NC}"; sleep 1; show_menu ;;
        5) stop_all_tunnels ;;
        6) install_cloudflared_system ;;
        7) show_config ;;
        8) show_about ;;
        9) change_language ;;
        0) exit 0 ;;
        *) 
            echo -e "${RED}[!] $(get_text invalid_option)${NC}"
            sleep 1
            show_menu 
            ;;
    esac
}

start_tunnel() {
    print_banner
    
    # Perguntar porta
    while true; do
        echo -e "${CYAN}[?] $(get_text enter_port)${NC}"
        read -r PORT
        if [ -z "$PORT" ]; then
            PORT=$DEFAULT_PORT
        fi
        
        if [[ ! "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
            echo -e "${RED}[!] Porta inválida. Use um número entre 1 e 65535.${NC}"
            continue
        fi
        
        # Verificar se porta está em uso
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${YELLOW}[!] $(get_text port_in_use "$PORT")${NC}"
            echo -e "${CYAN}[?] $(get_text stop_port "$PORT")${NC}"
            read -r kill_process
            if [[ "$kill_process" =~ ^[SsYy] ]]; then
                sudo fuser -k $PORT/tcp >/dev/null 2>&1
                sleep 2
                break
            else
                continue
            fi
        else
            break
        fi
    done
    
    # Escolher diretório
    echo -e "${CYAN}[?] $(get_text dir_selection)${NC}"
    echo -e "  $(get_text dir_option1)"
    echo -e "  $(get_text dir_option2)"
    echo -e "  $(get_text dir_option3)"
    echo -e "${CYAN}[?] $(get_text choose_dir)${NC}"
    read -r dir_choice
    
    case $dir_choice in
        2)
            DIR=$DEFAULT_DIR
            mkdir -p "$DIR"
            echo -e "${GREEN}[+] $(get_text using_default "$DIR")${NC}"
            ;;
        3)
            echo -e "${CYAN}[?] $(get_text enter_dir)${NC}"
            read -r custom_dir
            DIR=$(eval echo "$custom_dir")
            mkdir -p "$DIR"
            echo -e "${GREEN}[+] $(get_text using_custom "$DIR")${NC}"
            ;;
        *)
            DIR=$(pwd)
            echo -e "${GREEN}[+] $(get_text using_current "$DIR")${NC}"
            ;;
    esac
    
    # Verificar dependências
    check_dependencies
    
    # Criar página HTML simples
    if [ ! -f "$DIR/index.html" ]; then
        cat > "$DIR/index.html" << HTML
<!DOCTYPE html>
<html>
<head><title>Tunnel on port $PORT</title></head>
<body>
<h1>🚀 Tunnel Active - Port $PORT</h1>
<p>Server directory: $DIR</p>
<p>Created with Tunnel Manager v$VERSION</p>
</body>
</html>
HTML
    fi
    
    # Iniciar servidor HTTP
    echo -e "${CYAN}[*] $(get_text starting_http "$PORT")${NC}"
    cd "$DIR"
    python3 -m http.server "$PORT" > /tmp/tunnel-http.log 2>&1 &
    HTTP_PID=$!
    echo $HTTP_PID > "$PID_FILE"
    
    sleep 2
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        echo -e "${GREEN}[+] $(get_text http_started "$HTTP_PID")${NC}"
    else
        echo -e "${RED}[!] Falha ao iniciar servidor HTTP${NC}"
        return 1
    fi
    
    # Iniciar Cloudflared
    echo -e "${CYAN}[*] Iniciando Cloudflared Tunnel...${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}Aguardando URL do Cloudflared...${NC}"
    echo -e "${CYAN}Pressione Ctrl+C para parar${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    
    # Executar Cloudflared
    if command -v cloudflared &> /dev/null; then
        cloudflared tunnel --url "http://localhost:$PORT"
    elif [ -f "/tmp/cloudflared" ]; then
        /tmp/cloudflared tunnel --url "http://localhost:$PORT"
    else
        echo -e "${RED}[!] Cloudflared não encontrado${NC}"
        return 1
    fi
}

start_current_dir_tunnel() {
    print_banner
    DIR=$(pwd)
    echo -e "${GREEN}[+] $(get_text using_current "$DIR")${NC}"
    
    # Reutilizar lógica do start_tunnel
    start_tunnel
}

check_dependencies() {
    echo -e "${CYAN}[*] $(get_text checking_deps)${NC}"
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[!] Python3 não encontrado. Instale com: sudo apt install python3${NC}"
        exit 1
    else
        echo -e "${GREEN}[+] $(get_text python_found)${NC}"
    fi
    
    # Verificar Cloudflared
    if ! command -v cloudflared &> /dev/null && [ ! -f "/tmp/cloudflared" ]; then
        echo -e "${YELLOW}[!] $(get_text cloudflared_not_found)${NC}"
        download_cloudflared
    else
        echo -e "${GREEN}[+] $(get_text cloudflared_found)${NC}"
    fi
}

download_cloudflared() {
    echo -e "${YELLOW}[*] $(get_text downloading_cf)${NC}"
    
    if command -v curl &> /dev/null; then
        curl -L "$CLOUDFLARED_URL" -o "/tmp/cloudflared"
    elif command -v wget &> /dev/null; then
        wget "$CLOUDFLARED_URL" -O "/tmp/cloudflared"
    else
        echo -e "${RED}[!] Nem curl nem wget encontrados. Instale um deles.${NC}"
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        chmod +x "/tmp/cloudflared"
        echo -e "${GREEN}[+] Cloudflared baixado para /tmp/cloudflared${NC}"
    else
        echo -e "${RED}[!] Falha ao baixar Cloudflared${NC}"
        exit 1
    fi
}

stop_all_tunnels() {
    echo -e "${YELLOW}[*] Parando todos os túneis...${NC}"
    pkill -f "http.server" 2>/dev/null
    pkill -f "cloudflared" 2>/dev/null
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    echo -e "${GREEN}[+] Todos os túneis foram parados${NC}"
    sleep 2
    show_menu
}

install_cloudflared_system() {
    echo -e "${CYAN}[*] Instalando Cloudflared no sistema...${NC}"
    
    if [ ! -f "/tmp/cloudflared" ]; then
        download_cloudflared
    fi
    
    sudo mv "/tmp/cloudflared" "/usr/local/bin/cloudflared"
    sudo chmod +x "/usr/local/bin/cloudflared"
    echo -e "${GREEN}[+] Cloudflared instalado em /usr/local/bin/cloudflared${NC}"
    sleep 2
    show_menu
}

show_config() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}CONFIGURAÇÕES${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Versão:${NC} $VERSION"
    echo -e "${GREEN}Diretório padrão:${NC} $DEFAULT_DIR"
    echo -e "${GREEN}Porta padrão:${NC} $DEFAULT_PORT"
    echo -e "${GREEN}Idioma:${NC} $LANGUAGE"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    
    read -n 1 -s -r -p "$(get_text press_any_key)"
    show_menu
}

show_about() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}SOBRE${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "Tunnel Manager v$VERSION"
    echo -e "Script para criar túneis HTTP com Cloudflared"
    echo -e "Autor: Assistente de Pentest"
    echo -e "GitHub: github.com/pentest-tools"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    
    read -n 1 -s -r -p "$(get_text press_any_key)"
    show_menu
}

change_language() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}MUDAR IDIOMA${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "1) Português (PT)"
    echo -e "2) English (EN)"
    echo -e "\n${CYAN}Escolha (1-2): ${NC}"
    
    read -r lang_choice
    case $lang_choice in
        1) LANGUAGE="pt" ;;
        2) LANGUAGE="en" ;;
        *) echo -e "${RED}[!] Opção inválida${NC}"; sleep 1; show_menu; return ;;
    esac
    
    # Recarregar idioma
    load_language "$LANGUAGE"
    echo "LANGUAGE=$LANGUAGE" > "$CONFIG_FILE" 2>/dev/null
    echo -e "${GREEN}[+] Idioma alterado para: $LANGUAGE${NC}"
    sleep 1
    show_menu
}

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

# Garantir diretório de logs
mkdir -p "$LOG_DIR"

# Carregar configuração
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Carregar idioma
load_language "$LANGUAGE"

# Modo de execução
if [ $# -ge 1 ]; then
    # Modo direto: ./AutoTunnel.sh [PORTA] [DIRETÓRIO]
    PORT=${1:-$DEFAULT_PORT}
    if [ -n "$2" ]; then
        DIR="$2"
    else
        DIR=$(pwd)
    fi
    check_dependencies
    echo -e "${GREEN}[+] Iniciando túnel na porta $PORT, diretório: $DIR${NC}"
    cd "$DIR"
    python3 -m http.server "$PORT" &
    cloudflared tunnel --url "http://localhost:$PORT"
else
    # Modo interativo
    print_banner
    show_menu
fi
