# How to Use AutoTunnel

Este guia explica, de forma **completa e detalhada**, como utilizar o **AutoTunnel** desde a primeira execução até o gerenciamento diário de servidores e tunnels.

---

## 🚀 Primeira Execução

Ao abrir o AutoTunnel pela primeira vez:

* As dependências necessárias serão verificadas e instaladas automaticamente
* Os binários dos provedores de tunnel serão baixados, se necessário
* Os diretórios portáteis de configuração e dados serão criados
* Os arquivos iniciais de configuração serão gerados

Nenhuma configuração manual é exigida nesse primeiro momento.

Após essa etapa, o menu principal será exibido.

---

## 🧭 Menu Principal

O AutoTunnel é totalmente controlado por um menu interativo:

```
1) 🌐 Start HTTP server
2) 🚇 Start tunnel with server
3) 🔌 Start tunnel only
4) 🛑 Stop HTTP server
5) ✋ Stop tunnel
6) 📊 Current status
7) 📄 View logs
8) 🔗 View Active URLs
9) ⚙️ Settings
10) 🚪 Exit
```

Cada opção é explicada em detalhes abaixo.

---

## 🌐 1) Start HTTP server

Cria um servidor HTTP local.

Durante esse processo, você deverá:

* Escolher a **porta** onde o servidor irá rodar
* Selecionar o **diretório** que será servido

Após iniciado, o AutoTunnel exibirá um link no formato:

```
http://IP_LOCAL:PORTA
```

Esse endereço pode ser acessado:

* Pelo próprio navegador
* Por outras máquinas **na mesma rede local**

O diretório selecionado passa a funcionar como um servidor web:

* Hospedagem de arquivos
* Hospedagem de sites estáticos
* Download direto via navegador

O servidor permanece ativo até ser interrompido manualmente.

---

## 🚇 2) Start tunnel with server

Cria um servidor HTTP **e** inicia um tunnel automaticamente apontando para a porta do servidor.

Fluxo dessa opção:

1. O servidor HTTP é iniciado
2. Um tunnel é criado e vinculado à porta escolhida
3. Uma URL pública é gerada

O link gerado será acessível **de qualquer lugar da internet**, sem necessidade de:

* Redirecionamento de portas
* NAT
* Configuração no roteador

Essa opção é ideal para:

* Compartilhar arquivos externamente
* Demonstrações rápidas
* Ambientes de laboratório

---

## 🔌 3) Start tunnel only

Inicia **apenas o tunnel**, sem criar um servidor HTTP.

Você deverá informar:

* A **porta local** onde já existe um serviço rodando

O AutoTunnel criará uma URL pública apontando diretamente para esse serviço.

Casos de uso comuns:

* Expor serviços já existentes
* Utilizar a URL do tunnel em payloads
* Acessar serviços fora da rede local

Essa opção é especialmente útil para:

* Testes de segurança
* Laboratórios controlados
* Ambientes de desenvolvimento

---

## 🛑 4) Stop HTTP server

Interrompe um ou mais servidores HTTP ativos.

Você poderá:

* Visualizar os servidores em execução
* Selecionar qual deseja parar

O serviço é encerrado de forma segura.

---

## ✋ 5) Stop tunnel

Finaliza tunnels ativos.

Essa opção:

* Encerra o processo do tunnel
* Libera recursos
* Mantém o servidor HTTP intacto (se existir)

---

## 📊 6) Current status

Exibe o status atual do AutoTunnel.

Inclui informações como:

* Provedores de tunnel instalados
* Servidores HTTP ativos
* Tunnels em execução
* Portas utilizadas

Ideal para uma visão rápida do ambiente.

---

## 📄 7) View logs

Permite visualizar os logs gerados pelo AutoTunnel.

Inclui:

* Logs do servidor HTTP
* Requisições recebidas
* Downloads realizados
* Logs dos tunnels

Essa opção é essencial para:

* Debug
* Auditoria
* Monitoramento

---

## 🔗 8) View Active URLs

Mostra todas as URLs públicas e locais ativas.

A partir dessa tela, você pode:

* Copiar links rapidamente
* Acessar URLs no navegador
* Encerrar serviços associados

Funciona como um painel central de gerenciamento.

---

## ⚙️ 9) Settings

Permite configurar o comportamento do AutoTunnel.

Entre as opções disponíveis:

* Alterar o idioma padrão
* Definir diretório padrão de hospedagem
* Configurar token do ngrok
* Definir porta padrão

As configurações são salvas automaticamente.

---

## 🚪 10) Exit

Encerra o AutoTunnel de forma segura.

Ao sair:

* Todos os servidores ativos são encerrados
* Todos os tunnels são finalizados
* O estado é salvo corretamente

---

## ✅ Considerações Finais

O AutoTunnel foi projetado para ser:

* Simples de usar
* Seguro em ambientes controlados
* Totalmente portátil

Utilize sempre de forma responsável, especialmente ao expor serviços à internet.

---

Happy tunneling 🚀
