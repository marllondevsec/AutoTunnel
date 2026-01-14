cat > ~/modelos/tunnel-manager.sh << 'EOF'
#!/bin/bash
# =============================================================================
# TUNNEL MANAGER - HTTP Server + Cloudflared Tunnel
# Script robusto com verificações, logging e opções avançadas
# Suporte: Português (pt) e Inglês (en)
# =============================================================================

# Obter diretório onde o script está instalado
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Configurações
VERSION="2.0.0"
CONFIG_FILE="$HOME/.tunnel-manager.conf"
LOG_DIR="$HOME/.tunnel-manager/logs"
PID_FILE="/tmp/tunnel-manager.pid"
DEFAULT_PORT=1337
DEFAULT_DIR="$SCRIPT_DIR/www"  # Agora relativo ao diretório do script
CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"

# Idioma padrão (será configurado na inicialização)
LANGUAGE="pt"
declare -A TEXT

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# =============================================================================
# SISTEMA DE IDIOMAS
# =============================================================================

load_language() {
    local lang=$1
    
    if [[ "$lang" == "en" ]]; then
        # English
        TEXT=(
            # Menu
            ["menu_title"]="TUNNEL MANAGER v$VERSION"
            ["menu_options"]="MENU OPTIONS"
            ["menu_1"]="Start new tunnel"
            ["menu_2"]="Start tunnel in current directory"
            ["menu_3"]="View active tunnels"
            ["menu_4"]="View logs"
            ["menu_5"]="Stop all tunnels"
            ["menu_6"]="Install Cloudflared (system)"
            ["menu_7"]="Settings"
            ["menu_8"]="About"
            ["menu_9"]="Change language"
            ["menu_0"]="Exit"
            ["menu_choose"]="Choose an option: "
            
            # Common
            ["press_any_key"]="Press any key to continue..."
            ["invalid_option"]="Invalid option"
            ["loading"]="Loading..."
            ["success"]="Success"
            ["error"]="Error"
            ["warning"]="Warning"
            ["info"]="Information"
            ["port"]="Port"
            ["directory"]="Directory"
            ["current_dir"]="Current directory"
            ["status"]="Status"
            ["online"]="ONLINE"
            ["offline"]="OFFLINE"
            ["active"]="Active"
            ["inactive"]="Inactive"
            ["url"]="URL"
            ["pid"]="PID"
            ["process"]="Process"
            ["command"]="Command"
            ["unknown"]="Unknown"
            
            # Tunnel creation
            ["tunnel_creation"]="Starting HTTP Server + Cloudflared Tunnel"
            ["enter_port"]="Enter HTTP server port (default: $DEFAULT_PORT): "
            ["port_in_use"]="Port $1 is already in use"
            ["stop_port"]="Stop process on port $1? (y/N): "
            ["enter_another_port"]="Enter another port: "
            
            ["dir_selection"]="HTTP server directory:"
            ["dir_option1"]="1) Use current directory ($(pwd))"
            ["dir_option2"]="2) Use default directory ($DEFAULT_DIR)"
            ["dir_option3"]="3) Specify another directory"
            ["choose_dir"]="Choose (1-3, default: 1): "
            ["enter_dir"]="Enter directory path: "
            ["using_current"]="Using current directory: $1"
            ["using_default"]="Using default directory: $1"
            ["using_custom"]="Using directory: $1"
            
            ["tunnel_name"]="Tunnel name (optional, for identification): "
            
            # Services
            ["starting_http"]="Starting HTTP Server on port $1..."
            ["http_started"]="HTTP Server started (PID: $1)"
            ["http_failed"]="Failed to start HTTP Server"
            ["starting_tunnel"]="Starting Cloudflared Tunnel..."
            ["waiting_url"]="Waiting for Cloudflared URL..."
            ["press_ctrl_c"]="Press Ctrl+C to stop"
            ["tunnel_created"]="✅ TUNNEL CREATED SUCCESSFULLY!"
            ["tunnel_url"]="URL: $1"
            ["local_url"]="Local: http://localhost:$2"
            ["server_dir"]="Directory: $3"
            ["files_in_dir"]="Files in directory:"
            
            ["useful_commands"]="Useful commands:"
            ["test_cmd"]="Test: curl $1"
            ["download_cmd"]="Download: wget $1"
            ["local_cmd"]="Local port: http://localhost:$2"
            ["list_cmd"]="List files: ls -la \"$3\""
            
            # Dependencies
            ["checking_deps"]="Checking dependencies..."
            ["python_found"]="Python3 found"
            ["python_not_found"]="Python not found. Install with: sudo apt install python3"
            ["cloudflared_found"]="Cloudflared found in PATH"
            ["cloudflared_not_found"]="Cloudflared not found"
            ["downloading_cf"]="Downloading Cloudflared..."
            ["install_permanent"]="Install Cloudflared permanently? (y/N): "
            ["cf_installed"]="Cloudflared installed to /usr/local/bin/"
            ["using_temp"]="Using temporary Cloudflared"
            ["download_failed"]="Failed to download Cloudflared"
            ["curl_wget_not_found"]="Neither curl nor wget found. Install one of them."
            
            # Active tunnels
            ["active_tunnels"]="ACTIVE TUNNELS"
            ["http_servers"]="✓ HTTP Servers:"
            ["no_http_servers"]="⚠ No HTTP Servers active"
            ["cf_tunnels"]="✓ Cloudflared Tunnels:"
            ["no_cf_tunnels"]="⚠ No Cloudflared Tunnels active"
            ["last_url"]="✓ Last generated URL:"
            ["tunnel_info"]="✓ Last tunnel information:"
            
            # Logs
            ["available_logs"]="AVAILABLE LOGS"
            ["log_files"]="Log files:"
            ["no_logs"]="No logs available"
            ["view_log"]="View which log? (filename or ENTER to go back): "
            ["file_not_found"]="File not found"
            
            # Settings
            ["settings"]="SETTINGS"
            ["version"]="Version"
            ["python"]="Python"
            ["cloudflared"]="Cloudflared"
            ["downloader"]="Downloader"
            ["log_dir"]="Log directory"
            ["default_dir"]="Default directory"
            ["default_port"]="Default port"
            ["change_settings"]="Change settings? (y/N): "
            ["new_port"]="New default port (current: $1): "
            ["new_dir"]="New default directory (current: $1): "
            ["port_changed"]="Default port changed to: $1"
            ["dir_changed"]="Default directory changed to: $1"
            
            # About
            ["about"]="ABOUT"
            ["description"]="A robust script to create HTTP tunnels via Cloudflared with automatic checks and friendly interface."
            ["features"]="Features:"
            ["feature1"]="• Automatic dependency checking"
            ["feature2"]="• Automatic Cloudflared download"
            ["feature3"]="• Automatic HTML page"
            ["feature4"]="• Complete logging system"
            ["feature5"]="• Interactive colored menu"
            ["feature6"]="• Port checking"
            ["feature7"]="• Current directory support"
            ["feature8"]="• Active tunnel listing"
            ["feature9"]="• Safe service stopping"
            ["feature10"]="• Multi-language support"
            
            ["new_in_version"]="New in v$VERSION:"
            ["new_feature1"]="• Multi-language support (PT/EN)"
            ["new_feature2"]="• Better tunnel listing"
            ["new_feature3"]="• Detailed tunnel information"
            
            ["quick_commands"]="Quick commands:"
            ["cmd1"]="tunnel-manager             # Interactive menu"
            ["cmd2"]="tunnel-manager 8080 ~/site # Direct mode"
            ["cmd3"]="tunnel                     # Shortcut (if configured)"
            
            ["author"]="Author"
            ["github"]="GitHub"
            
            # Language selection
            ["language"]="LANGUAGE"
            ["current_language"]="Current language: $1"
            ["select_language"]="Select language:"
            ["lang_option1"]="1) Português (Portuguese)"
            ["lang_option2"]="2) English (English)"
            ["choose_language"]="Choose language (1-2): "
            ["language_changed"]="Language changed to: $1"
            
            # Installation
            ["installing_cf"]="Installing Cloudflared system-wide..."
            ["cf_installed_system"]="Cloudflared installed to /usr/local/bin/"
            ["create_alias"]="Create 'tunnel' shortcut? (y/N): "
            ["alias_added"]="Shortcut 'tunnel' added to .bashrc"
            ["run_source"]="Run 'source ~/.bashrc' to load shortcut"
            
            # Cleanup
            ["stopping_services"]="Stopping services..."
            ["services_stopped"]="Services stopped successfully"
            ["stopping_all"]="Stopping all tunnels..."
            ["all_stopped"]="All tunnels stopped"
        )
    else
        # Português (padrão)
        TEXT=(
            # Menu
            ["menu_title"]="TUNNEL MANAGER v$VERSION"
            ["menu_options"]="MENU DE OPÇÕES"
            ["menu_1"]="Iniciar novo túnel"
            ["menu_2"]="Iniciar túnel no diretório atual"
            ["menu_3"]="Ver túneis ativos"
            ["menu_4"]="Ver logs"
            ["menu_5"]="Parar todos os túneis"
            ["menu_6"]="Instalar Cloudflared (sistema)"
            ["menu_7"]="Configurações"
            ["menu_8"]="Sobre"
            ["menu_9"]="Mudar idioma"
            ["menu_0"]="Sair"
            ["menu_choose"]="Escolha uma opção: "
            
            # Comum
            ["press_any_key"]="Pressione qualquer tecla para continuar..."
            ["invalid_option"]="Opção inválida"
            ["loading"]="Carregando..."
            ["success"]="Sucesso"
            ["error"]="Erro"
            ["warning"]="Aviso"
            ["info"]="Informação"
            ["port"]="Porta"
            ["directory"]="Diretório"
            ["current_dir"]="Diretório atual"
            ["status"]="Status"
            ["online"]="ONLINE"
            ["offline"]="OFFLINE"
            ["active"]="Ativo"
            ["inactive"]="Inativo"
            ["url"]="URL"
            ["pid"]="PID"
            ["process"]="Processo"
            ["command"]="Comando"
            ["unknown"]="Desconhecido"
            
            # Criação de túnel
            ["tunnel_creation"]="Iniciando HTTP Server + Cloudflared Tunnel"
            ["enter_port"]="Porta para o servidor HTTP (padrão: $DEFAULT_PORT): "
            ["port_in_use"]="Porta $1 já está em uso"
            ["stop_port"]="Parar processo na porta $1? (s/N): "
            ["enter_another_port"]="Digite outra porta: "
            
            ["dir_selection"]="Diretório do servidor HTTP:"
            ["dir_option1"]="1) Usar diretório atual ($(pwd))"
            ["dir_option2"]="2) Usar diretório padrão ($DEFAULT_DIR)"
            ["dir_option3"]="3) Especificar outro diretório"
            ["choose_dir"]="Escolha (1-3, padrão: 1): "
            ["enter_dir"]="Digite o caminho do diretório: "
            ["using_current"]="Usando diretório atual: $1"
            ["using_default"]="Usando diretório padrão: $1"
            ["using_custom"]="Usando diretório: $1"
            
            ["tunnel_name"]="Nome do túnel (opcional, para identificação): "
            
            # Serviços
            ["starting_http"]="Iniciando HTTP Server na porta $1..."
            ["http_started"]="HTTP Server iniciado (PID: $1)"
            ["http_failed"]="Falha ao iniciar HTTP Server"
            ["starting_tunnel"]="Iniciando Cloudflared Tunnel..."
            ["waiting_url"]="Aguardando URL do Cloudflared..."
            ["press_ctrl_c"]="Pressione Ctrl+C para parar"
            ["tunnel_created"]="✅ TÚNEL CRIADO COM SUCESSO!"
            ["tunnel_url"]="URL: $1"
            ["local_url"]="Local: http://localhost:$2"
            ["server_dir"]="Diretório: $3"
            ["files_in_dir"]="Arquivos no diretório:"
            
            ["useful_commands"]="Comandos úteis:"
            ["test_cmd"]="Testar: curl $1"
            ["download_cmd"]="Download: wget $1"
            ["local_cmd"]="Porta local: http://localhost:$2"
            ["list_cmd"]="Listar arquivos: ls -la \"$3\""
            
            # Dependências
            ["checking_deps"]="Verificando dependências..."
            ["python_found"]="Python3 encontrado"
            ["python_not_found"]="Python não encontrado. Instale com: sudo apt install python3"
            ["cloudflared_found"]="Cloudflared encontrado no PATH"
            ["cloudflared_not_found"]="Cloudflared não encontrado"
            ["downloading_cf"]="Baixando Cloudflared..."
            ["install_permanent"]="Instalar Cloudflared permanentemente? (s/N): "
            ["cf_installed"]="Cloudflared instalado em /usr/local/bin/"
            ["using_temp"]="Usando Cloudflared temporário"
            ["download_failed"]="Falha ao baixar Cloudflared"
            ["curl_wget_not_found"]="Nem curl nem wget encontrados. Instale um deles."
            
            # Túneis ativos
            ["active_tunnels"]="TÚNEIS ATIVOS"
            ["http_servers"]="✓ HTTP Servers:"
            ["no_http_servers"]="⚠ Nenhum HTTP Server ativo"
            ["cf_tunnels"]="✓ Cloudflared Tunnels:"
            ["no_cf_tunnels"]="⚠ Nenhum Cloudflared Tunnel ativo"
            ["last_url"]="✓ Última URL gerada:"
            ["tunnel_info"]="✓ Informações do último túnel:"
            
            # Logs
            ["available_logs"]="LOGS DISPONÍVEIS"
            ["log_files"]="Arquivos de log:"
            ["no_logs"]="Nenhum log disponível"
            ["view_log"]="Ver qual log? (nome ou ENTER para voltar): "
            ["file_not_found"]="Arquivo não encontrado"
            
            # Configurações
            ["settings"]="CONFIGURAÇÕES"
            ["version"]="Versão"
            ["python"]="Python"
            ["cloudflared"]="Cloudflared"
            ["downloader"]="Downloader"
            ["log_dir"]="Diretório de logs"
            ["default_dir"]="Diretório padrão"
            ["default_port"]="Porta padrão"
            ["change_settings"]="Deseja alterar alguma configuração? (s/N): "
            ["new_port"]="Nova porta padrão (atual: $1): "
            ["new_dir"]="Novo diretório padrão (atual: $1): "
            ["port_changed"]="Porta padrão alterada para: $1"
            ["dir_changed"]="Diretório padrão alterado para: $1"
            
            # Sobre
            ["about"]="SOBRE"
            ["description"]="Um script robusto para criar túneis HTTP via Cloudflared com verificações automáticas e interface amigável."
            ["features"]="Features:"
            ["feature1"]="• Verificação automática de dependências"
            ["feature2"]="• Download automático do Cloudflared"
            ["feature3"]="• Página HTML automática"
            ["feature4"]="• Sistema de logging completo"
            ["feature5"]="• Menu interativo colorido"
            ["feature6"]="• Verificação de portas"
            ["feature7"]="• Suporte a diretório atual"
            ["feature8"]="• Listagem de túneis ativos"
            ["feature9"]="• Parada segura de serviços"
            ["feature10"]="• Suporte a múltiplos idiomas"
            
            ["new_in_version"]="Novo na v$VERSION:"
            ["new_feature1"]="• Suporte a múltiplos idiomas (PT/EN)"
            ["new_feature2"]="• Melhor listagem de túneis"
            ["new_feature3"]="• Informações detalhadas do túnel"
            
            ["quick_commands"]="Comandos rápidos:"
            ["cmd1"]="tunnel-manager             # Menu interativo"
            ["cmd2"]="tunnel-manager 8080 ~/site # Modo direto"
            ["cmd3"]="tunnel                     # Atalho (se configurado)"
            
            ["author"]="Autor"
            ["github"]="GitHub"
            
            # Seleção de idioma
            ["language"]="IDIOMA"
            ["current_language"]="Idioma atual: $1"
            ["select_language"]="Selecione o idioma:"
            ["lang_option1"]="1) Português (Portuguese)"
            ["lang_option2"]="2) English (English)"
            ["choose_language"]="Escolha o idioma (1-2): "
            ["language_changed"]="Idioma alterado para: $1"
            
            # Instalação
            ["installing_cf"]="Instalando Cloudflared no sistema..."
            ["cf_installed_system"]="Cloudflared instalado em /usr/local/bin/"
            ["create_alias"]="Criar atalho 'tunnel'? (s/N): "
            ["alias_added"]="Atalho 'tunnel' adicionado ao .bashrc"
            ["run_source"]="Execute 'source ~/.bashrc' para carregar o atalho"
            
            # Cleanup
            ["stopping_services"]="Parando serviços..."
            ["services_stopped"]="Serviços parados com sucesso"
            ["stopping_all"]="Parando todos os túneis..."
            ["all_stopped"]="Todos os túneis foram parados"
        )
    fi
}

# Função para obter texto com parâmetros
get_text() {
    local key=$1
    local text="${TEXT[$key]}"
    
    # Substituir parâmetros se fornecidos
    shift
    for ((i=1; i<=$#; i++)); do
        text="${text//\$$i/${!i}}"
    done
    
    echo "$text"
}

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

print_banner() {
    clear
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   ████████╗██╗   ██╗███╗   ██╗███╗   ██╗███████╗██╗      ║
║   ╚══██╔══╝██║   ██║████╗  ██║████╗  ██║██╔════╝██║      ║
║      ██║   ██║   ██║██╔██╗ ██║██╔██╗ ██║█████╗  ██║      ║
║      ██║   ██║   ██║██║╚██╗██║██║╚██╗██║██╔══╝  ██║      ║
║      ██║   ╚██████╔╝██║ ╚████║██║ ╚████║███████╗███████╗ ║
║      ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚══════╝ ║
╠═══════════════════════════════════════════════════════════╣
║                  CLOUDFLARED TUNNEL MANAGER               ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "menu_title")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
}

log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-d %H:%M:%S')
    local log_entry="[$timestamp] [$level] $message"
    
    echo -e "${log_entry}" | tee -a "$LOG_FILE"
}

check_dependencies() {
    echo -e "${CYAN}[*] $(get_text "checking_deps")${NC}"
    log_message "INFO" "$(get_text "checking_deps")"
    
    # Verificar Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        log_message "SUCCESS" "$(get_text "python_found")"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        log_message "SUCCESS" "$(get_text "python_found")"
    else
        log_message "ERROR" "$(get_text "python_not_found")"
        echo -e "${RED}[!] $(get_text "python_not_found")${NC}"
        exit 1
    fi
    
    # Verificar Cloudflared
    if command -v cloudflared &> /dev/null; then
        CLOUDFLARED_CMD="cloudflared"
        log_message "SUCCESS" "$(get_text "cloudflared_found")"
    elif [ -f "/usr/local/bin/cloudflared" ]; then
        CLOUDFLARED_CMD="/usr/local/bin/cloudflared"
        log_message "SUCCESS" "$(get_text "cloudflared_found")"
    elif [ -f "/bin/cloudflared" ]; then
        CLOUDFLARED_CMD="/bin/cloudflared"
        log_message "SUCCESS" "$(get_text "cloudflared_found")"
    elif [ -f "$HOME/bin/cloudflared" ]; then
        CLOUDFLARED_CMD="$HOME/bin/cloudflared"
        log_message "SUCCESS" "$(get_text "cloudflared_found")"
    else
        log_message "WARN" "$(get_text "cloudflared_not_found")"
        echo -e "${YELLOW}[!] $(get_text "cloudflared_not_found")${NC}"
        download_cloudflared
    fi
    
    # Verificar curl/wget
    if command -v curl &> /dev/null; then
        DOWNLOAD_CMD="curl -L -o"
        log_message "SUCCESS" "curl found"
    elif command -v wget &> /dev/null; then
        DOWNLOAD_CMD="wget -O"
        log_message "SUCCESS" "wget found"
    else
        log_message "ERROR" "$(get_text "curl_wget_not_found")"
        echo -e "${RED}[!] $(get_text "curl_wget_not_found")${NC}"
        exit 1
    fi
}

download_cloudflared() {
    echo -e "${YELLOW}[*] $(get_text "downloading_cf")${NC}"
    log_message "INFO" "$(get_text "downloading_cf")"
    
    # Criar diretório bin se não existir
    mkdir -p "$HOME/bin"
    
    # Download do cloudflared
    if [ "$DOWNLOAD_CMD" == "curl -L -o" ]; then
        curl -L "$CLOUDFLARED_URL" -o "/tmp/cloudflared"
    else
        wget "$CLOUDFLARED_URL" -O "/tmp/cloudflared"
    fi
    
    if [ $? -eq 0 ]; then
        chmod +x "/tmp/cloudflared"
        CLOUDFLARED_CMD="/tmp/cloudflared"
        
        # Perguntar se quer instalar permanentemente
        echo -e "${CYAN}[?] $(get_text "install_permanent")${NC}"
        read -r install_perm
        if [[ "$install_perm" =~ ^[SsYy]([Ii])?$ ]]; then
            sudo mv "/tmp/cloudflared" "/usr/local/bin/cloudflared"
            CLOUDFLARED_CMD="cloudflared"
            log_message "SUCCESS" "$(get_text "cf_installed")"
            echo -e "${GREEN}[+] $(get_text "cf_installed")${NC}"
        else
            log_message "INFO" "$(get_text "using_temp")"
        fi
    else
        log_message "ERROR" "$(get_text "download_failed")"
        echo -e "${RED}[!] $(get_text "download_failed")${NC}"
        exit 1
    fi
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[!] $(get_text "port_in_use" "$port")${NC}"
        echo -e "${CYAN}[?] $(get_text "stop_port" "$port")${NC}"
        read -r kill_process
        if [[ "$kill_process" =~ ^[SsYy]([Ii])?$ ]]; then
            sudo fuser -k $port/tcp >/dev/null 2>&1
            sleep 2
            return 0
        else
            return 1
        fi
    fi
    return 0
}

get_user_input() {
    # Porta
    echo -e "${CYAN}[?] $(get_text "enter_port")${NC}"
    read -r port_input
    if [ -z "$port_input" ]; then
        PORT=$DEFAULT_PORT
    else
        PORT=$port_input
    fi
    
    # Verificar porta
    while ! check_port $PORT; do
        echo -e "${CYAN}[?] $(get_text "enter_another_port")${NC}"
        read -r PORT
    done
    
    # Diretório
    echo -e "${CYAN}[?] $(get_text "dir_selection")${NC}"
    echo -e "  $(get_text "dir_option1")"
    echo -e "  $(get_text "dir_option2")"
    echo -e "  $(get_text "dir_option3")"
    echo -e "${CYAN}[?] $(get_text "choose_dir")${NC}"
    read -r dir_choice
    
    case $dir_choice in
        1)
            DIR=$(pwd)
            echo -e "${GREEN}[+] $(get_text "using_current" "$DIR")${NC}"
            ;;
        2)
            DIR=$DEFAULT_DIR
            mkdir -p "$DIR"
            echo -e "${GREEN}[+] $(get_text "using_default" "$DIR")${NC}"
            ;;
        3)
            echo -e "${CYAN}[?] $(get_text "enter_dir")${NC}"
            read -r custom_dir
            DIR=$(eval echo "$custom_dir")
            mkdir -p "$DIR"
            echo -e "${GREEN}[+] $(get_text "using_custom" "$DIR")${NC}"
            ;;
        *)
            DIR=$(pwd)
            echo -e "${GREEN}[+] $(get_text "using_current" "$DIR")${NC}"
            ;;
    esac
    
    # Nome do túnel (opcional)
    echo -e "${CYAN}[?] $(get_text "tunnel_name")${NC}"
    read -r tunnel_name
}

create_index_page() {
    local port=$1
    local dir=$2
    
    if [ ! -f "$dir/index.html" ]; then
        # Determinar título baseado no idioma
        local title
        if [[ "$LANGUAGE" == "en" ]]; then
            title="🚀 Cloudflared Tunnel - Port $port"
        else
            title="🚀 Tunnel Cloudflared - Porta $port"
        fi
        
        cat > "$dir/index.html" << HTML
<!DOCTYPE html>
<html lang="${LANGUAGE}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            max-width: 800px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        h1 { 
            font-size: 2.5rem; 
            margin-bottom: 20px; 
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            background: #10b981;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        .url-box {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            border: 2px solid rgba(255, 255, 255, 0.1);
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .info-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .info-card h3 {
            color: #c4b5fd;
            margin-bottom: 10px;
        }
        .buttons {
            display: flex;
            gap: 10px;
            margin-top: 30px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 24px;
            background: #4f46e5;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }
        .btn:hover {
            background: #4338ca;
            transform: translateY(-2px);
        }
        .btn.copy {
            background: #10b981;
        }
        .btn.copy:hover {
            background: #0da271;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>$title</h1>
        <p>$( [[ "$LANGUAGE" == "en" ]] && echo "Your server is running and accessible through Cloudflare tunnel." || echo "Seu servidor está rodando e acessível através do túnel Cloudflare." )</p>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>📍 $(get_text "port")</h3>
                <p id="port">$port</p>
            </div>
            <div class="info-card">
                <h3>📁 $(get_text "directory")</h3>
                <p id="dir">${dir##*/}</p>
            </div>
            <div class="info-card">
                <h3>📡 $(get_text "status")</h3>
                <span class="status">● $(get_text "online")</span>
            </div>
        </div>
        
        <h2>🔗 $(get_text "url"):</h2>
        <div class="url-box" id="url-box">
            $( [[ "$LANGUAGE" == "en" ]] && echo "Waiting for Cloudflared URL..." || echo "Aguardando URL do Cloudflared..." )
        </div>
        
        <div class="buttons">
            <button class="btn copy" onclick="copyURL()">📋 $( [[ "$LANGUAGE" == "en" ]] && echo "Copy URL" || echo "Copiar URL" )</button>
            <a href="#" class="btn" onclick="refreshPage()">🔄 $( [[ "$LANGUAGE" == "en" ]] && echo "Refresh" || echo "Atualizar" )</a>
            <a href="/" class="btn">🏠 $( [[ "$LANGUAGE" == "en" ]] && echo "Home" || echo "Home" )</a>
        </div>
        
        <p style="margin-top: 30px; opacity: 0.8; font-size: 0.9rem;">
            $( [[ "$LANGUAGE" == "en" ]] && echo "Created with Tunnel Manager v$VERSION" || echo "Criado com Tunnel Manager v$VERSION" ) • $(date +'%d/%m/%Y %H:%M')
        </p>
    </div>
    
    <script>
        function copyURL() {
            const url = document.getElementById('url-box').innerText;
            navigator.clipboard.writeText(url).then(() => {
                alert('$( [[ "$LANGUAGE" == "en" ]] && echo "URL copied to clipboard!" || echo "URL copiada para a área de transferência!" )');
            });
        }
        
        function refreshPage() {
            location.reload();
        }
        
        // Tentar detectar URL automaticamente após 2 segundos
        setTimeout(() => {
            const path = window.location.href;
            if (path.includes('trycloudflare.com')) {
                document.getElementById('url-box').innerText = path;
            }
        }, 2000);
        
        // Auto-refresh a cada 5 segundos até ter URL
        let refreshCount = 0;
        const refreshInterval = setInterval(() => {
            const urlBox = document.getElementById('url-box');
            if (!urlBox.innerText.includes('trycloudflare.com') && refreshCount < 10) {
                refreshCount++;
                fetch(window.location.href)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const newUrl = doc.getElementById('url-box')?.innerText;
                        if (newUrl && newUrl.includes('trycloudflare.com')) {
                            urlBox.innerText = newUrl;
                            clearInterval(refreshInterval);
                        }
                    });
            } else {
                clearInterval(refreshInterval);
            }
        }, 5000);
    </script>
</body>
</html>
HTML
        log_message "SUCCESS" "Página index.html criada em $dir"
    fi
}

start_services() {
    # Iniciar HTTP Server
    echo -e "${CYAN}[*] $(get_text "starting_http" "$PORT")${NC}"
    log_message "INFO" "$(get_text "starting_http" "$PORT")"
    
    cd "$DIR"
    $PYTHON_CMD -m http.server "$PORT" > "$LOG_DIR/http-server.log" 2>&1 &
    HTTP_PID=$!
    echo $HTTP_PID > "$PID_FILE"
    
    # Aguardar servidor iniciar
    sleep 3
    
    # Verificar se servidor está rodando
    if curl -s "http://localhost:$PORT" > /dev/null 2>&1; then
        log_message "SUCCESS" "$(get_text "http_started" "$HTTP_PID")"
        echo -e "${GREEN}[+] $(get_text "http_started" "$HTTP_PID")${NC}"
    else
        log_message "ERROR" "$(get_text "http_failed")"
        echo -e "${RED}[!] $(get_text "http_failed")${NC}"
        return 1
    fi
    
    # Iniciar Cloudflared Tunnel
    echo -e "${CYAN}[*] $(get_text "starting_tunnel")${NC}"
    log_message "INFO" "$(get_text "starting_tunnel")"
    
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${MAGENTA}[*] $(get_text "waiting_url")${NC}"
    echo -e "${CYAN}[*] $(get_text "press_ctrl_c")${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    
    # Capturar output do Cloudflared e extrair URL
    $CLOUDFLARED_CMD tunnel --url "http://localhost:$PORT" 2>&1 | \
    while IFS= read -r line; do
        echo "$line"
        
        # Extrair URL
        if [[ $line == *"https://"*".trycloudflare.com"* ]]; then
            TUNNEL_URL=$(echo "$line" | grep -o 'https://[^ ]*\.trycloudflare\.com')
            if [ ! -z "$TUNNEL_URL" ]; then
                echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
                echo -e "${BOLD}${GREEN}$(get_text "tunnel_created")${NC}"
                echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
                echo -e "${BOLD}$(get_text "tunnel_url" "$TUNNEL_URL")${NC}"
                echo -e "${BOLD}$(get_text "local_url" "$PORT")${NC}"
                echo -e "${BOLD}$(get_text "server_dir" "$DIR")${NC}"
                echo -e "${BOLD}$(get_text "files_in_dir")${NC}"
                ls -la "$DIR" | head -10
                echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
                echo -e "${CYAN}$(get_text "useful_commands")${NC}"
                echo -e "  $(get_text "test_cmd" "$TUNNEL_URL")"
                echo -e "  $(get_text "download_cmd" "$TUNNEL_URL")"
                echo -e "  $(get_text "local_cmd" "$PORT")"
                echo -e "  $(get_text "list_cmd" "$DIR")"
                echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
                
                # Salvar URL em arquivo
                echo "$TUNNEL_URL" > "$LOG_DIR/last_tunnel.url"
                
                # Salvar informações do túnel
                echo "URL: $TUNNEL_URL" > "$LOG_DIR/tunnel_info.txt"
                echo "Porta: $PORT" >> "$LOG_DIR/tunnel_info.txt"
                echo "Diretório: $DIR" >> "$LOG_DIR/tunnel_info.txt"
                echo "Data: $(date)" >> "$LOG_DIR/tunnel_info.txt"
                
                # Atualizar página HTML
                if [[ "$LANGUAGE" == "en" ]]; then
                    sed -i "s|Waiting for Cloudflared URL\.\.\.|$TUNNEL_URL|" "$DIR/index.html"
                else
                    sed -i "s|Aguardando URL do Cloudflared\.\.\.|$TUNNEL_URL|" "$DIR/index.html"
                fi
            fi
        fi
        
        # Logar erros importantes
        if [[ $line == *"ERROR"* ]] || [[ $line == *"ERR"* ]]; then
            log_message "ERROR" "$line"
        fi
    done
}

start_current_dir_tunnel() {
    echo -e "\n${CYAN}[*] $(get_text "menu_2")${NC}"
    
    # Configurar logging
    mkdir -p "$LOG_DIR"
    LOG_FILE="$LOG_DIR/tunnel-$(date +%Y%m%d-%H%M%S).log"
    
    # Verificar dependências
    check_dependencies
    
    # Usar diretório atual
    DIR=$(pwd)
    echo -e "${GREEN}[+] $(get_text "using_current" "$DIR")${NC}"
    
    # Mostrar conteúdo do diretório
    echo -e "${CYAN}[*] $(get_text "files_in_dir")${NC}"
    ls -la "$DIR" | head -15
    
    # Perguntar porta
    echo -e "${CYAN}[?] $(get_text "enter_port")${NC}"
    read -r port_input
    if [ -z "$port_input" ]; then
        PORT=$DEFAULT_PORT
    else
        PORT=$port_input
    fi
    
    # Verificar porta
    while ! check_port $PORT; do
        echo -e "${CYAN}[?] $(get_text "enter_another_port")${NC}"
        read -r PORT
    done
    
    # Criar página index se não existir
    create_index_page "$PORT" "$DIR"
    
    # Configurar trap para cleanup
    trap cleanup SIGINT SIGTERM
    
    # Iniciar serviços
    start_services
    
    # Se start_services retornar (erro ou interrupção)
    cleanup
}

cleanup() {
    echo -e "\n${YELLOW}[*] $(get_text "stopping_services")${NC}"
    log_message "INFO" "$(get_text "stopping_services")"
    
    # Parar HTTP Server
    if [ -f "$PID_FILE" ]; then
        HTTP_PID=$(cat "$PID_FILE")
        kill $HTTP_PID 2>/dev/null
        rm -f "$PID_FILE"
        log_message "INFO" "HTTP Server stopped"
    fi
    
    # Parar Cloudflared
    pkill -f "cloudflared.*$PORT" 2>/dev/null
    
    echo -e "${GREEN}[+] $(get_text "services_stopped")${NC}"
    exit 0
}

change_language() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "language")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    
    echo -e "$(get_text "current_language" "$LANGUAGE")"
    echo -e ""
    echo -e "${CYAN}$(get_text "select_language")${NC}"
    echo -e "  $(get_text "lang_option1")"
    echo -e "  $(get_text "lang_option2")"
    echo -e ""
    echo -e "${CYAN}$(get_text "choose_language")${NC}"
    
    read -r lang_choice
    case $lang_choice in
        1)
            LANGUAGE="pt"
            ;;
        2)
            LANGUAGE="en"
            ;;
        *)
            echo -e "${YELLOW}[!] $(get_text "invalid_option")${NC}"
            sleep 1
            show_menu
            return
            ;;
    esac
    
    # Recarregar textos
    load_language "$LANGUAGE"
    
    # Salvar configuração
    echo "LANGUAGE=$LANGUAGE" > "$CONFIG_FILE" 2>/dev/null
    
    echo -e "${GREEN}[+] $(get_text "language_changed" "$LANGUAGE")${NC}"
    sleep 1
    show_menu
}

show_menu() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "menu_options")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}1)${NC} $(get_text "menu_1")"
    echo -e "${GREEN}2)${NC} $(get_text "menu_2")"
    echo -e "${GREEN}3)${NC} $(get_text "menu_3")"
    echo -e "${GREEN}4)${NC} $(get_text "menu_4")"
    echo -e "${GREEN}5)${NC} $(get_text "menu_5")"
    echo -e "${GREEN}6)${NC} $(get_text "menu_6")"
    echo -e "${GREEN}7)${NC} $(get_text "menu_7")"
    echo -e "${GREEN}8)${NC} $(get_text "menu_8")"
    echo -e "${GREEN}9)${NC} $(get_text "menu_9")"
    echo -e "${GREEN}0)${NC} $(get_text "menu_0")"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$(get_text "menu_choose")${NC}"
    
    read -r option
    
    case $option in
        1) main ;;
        2) start_current_dir_tunnel ;;
        3) show_active_tunnels ;;
        4) show_logs ;;
        5) stop_all_tunnels ;;
        6) install_cloudflared_system ;;
        7) show_config ;;
        8) show_about ;;
        9) change_language ;;
        0) exit 0 ;;
        *) 
            echo -e "${RED}[!] $(get_text "invalid_option")${NC}"
            sleep 1
            show_menu 
            ;;
    esac
}

show_active_tunnels() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "active_tunnels")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    
    if pgrep -f "http.server" > /dev/null; then
        echo -e "${GREEN}$(get_text "http_servers")${NC}"
        pgrep -f "http.server" | while read pid; do
            port=$(ps -p $pid -o args= | grep -o '[0-9]*' | head -1)
            dir=$(ps -p $pid -o args= | grep -o 'http.server.*' | awk '{print $2}' | xargs dirname 2>/dev/null || echo "$(get_text "unknown")")
            echo -e "  $(get_text "pid"): $pid | $(get_text "port"): $port | $(get_text "directory"): $dir"
        done
    else
        echo -e "${YELLOW}$(get_text "no_http_servers")${NC}"
    fi
    
    if pgrep -f "cloudflared" > /dev/null; then
        echo -e "\n${GREEN}$(get_text "cf_tunnels")${NC}"
        pgrep -f "cloudflared" | while read pid; do
            cmd=$(ps -p $pid -o args=)
            echo -e "  $(get_text "pid"): $pid"
            echo "  $(get_text "command"): $cmd" | head -1
        done
    else
        echo -e "\n${YELLOW}$(get_text "no_cf_tunnels")${NC}"
    fi
    
    if [ -f "$LOG_DIR/last_tunnel.url" ]; then
        echo -e "\n${GREEN}$(get_text "last_url")${NC}"
        echo -e "  $(cat $LOG_DIR/last_tunnel.url)"
    fi
    
    if [ -f "$LOG_DIR/tunnel_info.txt" ]; then
        echo -e "\n${GREEN}$(get_text "tunnel_info")${NC}"
        cat "$LOG_DIR/tunnel_info.txt"
    fi
    
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    read -n 1 -s -r -p "$(get_text "press_any_key")"
    show_menu
}

show_logs() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "available_logs")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    
    if [ -d "$LOG_DIR" ]; then
        echo -e "${CYAN}$(get_text "log_files")${NC}"
        find "$LOG_DIR" -type f -name "*.log" -o -name "*.txt" -o -name "*.url" | while read file; do
            size=$(du -h "$file" | cut -f1)
            modified=$(stat -c %y "$file" | cut -d' ' -f1-2)
            echo -e "  $(basename "$file") - $size - $modified"
        done
        
        echo -e "\n${CYAN}[?] $(get_text "view_log")${NC}"
        read -r log_file
        if [ ! -z "$log_file" ]; then
            if [ -f "$LOG_DIR/$log_file" ]; then
                less "$LOG_DIR/$log_file"
            else
                # Tentar encontrar com caminho completo
                found_file=$(find "$LOG_DIR" -name "$log_file" | head -1)
                if [ ! -z "$found_file" ]; then
                    less "$found_file"
                else
                    echo -e "${RED}[!] $(get_text "file_not_found")${NC}"
                fi
            fi
        fi
    else
        echo -e "${YELLOW}$(get_text "no_logs")${NC}"
    fi
    
    show_menu
}

stop_all_tunnels() {
    echo -e "\n${YELLOW}[*] $(get_text "stopping_all")${NC}"
    log_message "INFO" "$(get_text "stopping_all")"
    
    pkill -f "http.server" 2>/dev/null
    pkill -f "cloudflared" 2>/dev/null
    
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
    
    echo -e "${GREEN}[+] $(get_text "all_stopped")${NC}"
    sleep 2
    show_menu
}

install_cloudflared_system() {
    echo -e "\n${CYAN}[*] $(get_text "installing_cf")${NC}"
    log_message "INFO" "$(get_text "installing_cf")"
    
    if [ "$DOWNLOAD_CMD" == "curl -L -o" ]; then
        sudo curl -L "$CLOUDFLARED_URL" -o "/usr/local/bin/cloudflared"
    else
        sudo wget "$CLOUDFLARED_URL" -O "/usr/local/bin/cloudflared"
    fi
    
    sudo chmod +x "/usr/local/bin/cloudflared"
    CLOUDFLARED_CMD="cloudflared"
    
    echo -e "${GREEN}[+] $(get_text "cf_installed_system")${NC}"
    
    # Criar atalho para usar direto do terminal
    echo -e "${CYAN}[?] $(get_text "create_alias")${NC}"
    read -r create_alias
    if [[ "$create_alias" =~ ^[SsYy]([Ii])?$ ]]; then
        echo "alias tunnel='$SCRIPT_DIR/tunnel-manager.sh'" >> "$HOME/.bashrc"
        echo -e "${GREEN}[+] $(get_text "alias_added")${NC}"
        echo -e "${YELLOW}[!] $(get_text "run_source")${NC}"
    fi
    
    sleep 2
    show_menu
}

show_config() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "settings")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}$(get_text "version"):${NC} $VERSION"
    echo -e "${GREEN}$(get_text "python"):${NC} $PYTHON_CMD"
    echo -e "${GREEN}$(get_text "cloudflared"):${NC} $CLOUDFLARED_CMD"
    echo -e "${GREEN}$(get_text "downloader"):${NC} $DOWNLOAD_CMD"
    echo -e "${GREEN}$(get_text "log_dir"):${NC} $LOG_DIR"
    echo -e "${GREEN}$(get_text "default_dir"):${NC} $DEFAULT_DIR"
    echo -e "${GREEN}$(get_text "default_port"):${NC} $DEFAULT_PORT"
    echo -e "${GREEN}$(get_text "current_dir"):${NC} $(pwd)"
    echo -e "${GREEN}$(get_text "language"):${NC} $LANGUAGE"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    
    echo -e "\n${CYAN}[?] $(get_text "change_settings")${NC}"
    read -r change_config
    if [[ "$change_config" =~ ^[SsYy]([Ii])?$ ]]; then
        echo -e "${CYAN}[?] $(get_text "new_port" "$DEFAULT_PORT")${NC}"
        read -r new_port
        if [ ! -z "$new_port" ]; then
            DEFAULT_PORT=$new_port
            echo -e "${GREEN}[+] $(get_text "port_changed" "$DEFAULT_PORT")${NC}"
        fi
        
        echo -e "${CYAN}[?] $(get_text "new_dir" "$DEFAULT_DIR")${NC}"
        read -r new_dir
        if [ ! -z "$new_dir" ]; then
            DEFAULT_DIR="$new_dir"
            mkdir -p "$DEFAULT_DIR"
            echo -e "${GREEN}[+] $(get_text "dir_changed" "$DEFAULT_DIR")${NC}"
        fi
    fi
    
    read -n 1 -s -r -p "$(get_text "press_any_key")"
    show_menu
}

show_about() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${WHITE}$(get_text "about")${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "$(get_text "description")"
    echo -e ""
    echo -e "${BOLD}$(get_text "features"):${NC}"
    echo -e "  $(get_text "feature1")"
    echo -e "  $(get_text "feature2")"
    echo -e "  $(get_text "feature3")"
    echo -e "  $(get_text "feature4")"
    echo -e "  $(get_text "feature5")"
    echo -e "  $(get_text "feature6")"
    echo -e "  $(get_text "feature7")"
    echo -e "  $(get_text "feature8")"
    echo -e "  $(get_text "feature9")"
    echo -e "  $(get_text "feature10")"
    echo -e ""
    echo -e "${BOLD}$(get_text "new_in_version"):${NC}"
    echo -e "  $(get_text "new_feature1")"
    echo -e "  $(get_text "new_feature2")"
    echo -e "  $(get_text "new_feature3")"
    echo -e ""
    echo -e "${BOLD}$(get_text "quick_commands"):${NC}"
    echo -e "  $(get_text "cmd1")"
    echo -e "  $(get_text "cmd2")"
    echo -e "  $(get_text "cmd3")"
    echo -e ""
    echo -e "${BOLD}$(get_text "author"):${NC} Assistente de Pentest"
    echo -e "${BOLD}$(get_text "github"):${NC} github.com/pentest-tools"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    read -n 1 -s -r -p "$(get_text "press_any_key")"
    show_menu
}

# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

main() {
    print_banner
    
    # Configurar logging
    mkdir -p "$LOG_DIR"
    LOG_FILE="$LOG_DIR/tunnel-$(date +%Y%m%d-%H%M%S).log"
    
    # Verificar dependências
    check_dependencies
    
    # Obter inputs do usuário
    get_user_input
    
    # Criar página index
    create_index_page "$PORT" "$DIR"
    
    # Configurar trap para cleanup
    trap cleanup SIGINT SIGTERM
    
    # Iniciar serviços
    start_services
    
    # Se start_services retornar (erro ou interrupção)
    cleanup
}

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

# Carregar configuração salva
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Carregar idioma
load_language "$LANGUAGE"

# Verificar se é modo interativo ou direto
if [[ $- == *i* ]] && [ $# -eq 0 ]; then
    # Modo interativo
    print_banner
    show_menu
else
    # Modo direto com argumentos
    if [ $# -ge 1 ]; then
        PORT=${1:-$DEFAULT_PORT}
        
        # Se segundo argumento for "current" ou ".", usar diretório atual
        if [[ "$2" == "current" ]] || [[ "$2" == "." ]] || [[ "$2" == "" ]]; then
            DIR=$(pwd)
            echo -e "${GREEN}[+] $(get_text "using_current" "$DIR")${NC}"
        else
            DIR=${2:-$DEFAULT_DIR}
        fi
        
        mkdir -p "$LOG_DIR"
        LOG_FILE="$LOG_DIR/tunnel-$(date +%Y%m%d-%H%M%S).log"
        check_dependencies
        create_index_page "$PORT" "$DIR"
        trap cleanup SIGINT SIGTERM
        start_services
    else
        main
    fi
fi
EOF

# Tornar executável
chmod +x ~/modelos/tunnel-manager.sh
