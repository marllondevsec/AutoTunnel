# Guia de Solução de Problemas e Reset

Este documento explica como resolver problemas comuns de inicialização e execução do **AutoTunnel**, especialmente nos casos em que a aplicação não inicia corretamente devido a arquivos de estado ou configuração corrompidos.

Antes de abrir uma issue ou solicitar correção, **siga os passos abaixo**.

---

## 🚨 Problema Comum: AutoTunnel Não Inicializa

Em algumas situações, o AutoTunnel pode falhar ao iniciar. Isso normalmente ocorre por causa de:

* Arquivos de estado corrompidos
* Arquivos JSON inválidos ou escritos parcialmente
* Encerramentos inesperados (fechamento forçado, queda do sistema)
* Metadados de processo ou PID antigos

Esses cenários impedem o carregamento correto do estado interno da aplicação.

---

## 🧠 Por Que Isso Acontece

O AutoTunnel armazena dados de execução e configuração em diretórios portáteis, incluindo:

* Processos ativos
* Tunnels em execução
* Metadados de servidores
* Configurações do usuário

Se algum desses arquivos for corrompido, a aplicação pode não conseguir inicializar corretamente.

A boa notícia: **isso pode ser resolvido com segurança, sem reinstalar o AutoTunnel**.

---

## 🧹 Procedimento Seguro de Reset (Recomendado)

Os passos abaixo realizam um reset do estado interno do AutoTunnel **sem remover os binários dos tunnels**.

### 1️⃣ Remover Arquivos de Estado Corrompidos

Execute os comandos abaixo:

```bash
# Remove dados de execução corrompidos (mantém os binários dos tunnels)
rm -f ~/.local/share/autotunnel/active_processes.json
rm -rf ~/.local/share/autotunnel/pids/*.json
rm -f ~/.config/autotunnel/config.json
```

O que esse procedimento faz:

* Remove o rastreamento de processos ativos
* Limpa referências antigas de PID
* Reseta a configuração para o padrão
* Mantém todos os binários de tunnels já baixados

---

### 2️⃣ Executar o AutoTunnel Novamente

Após a limpeza, inicie o AutoTunnel:

```bash
python3 AutoTunnel.py
```

Na inicialização, o AutoTunnel irá:

* Recriar arquivos de configuração ausentes
* Regenerar o estado interno de forma segura
* Iniciar normalmente

---

## ✅ Quando Usar Este Reset

Utilize este procedimento se:

* O AutoTunnel fecha ou trava ao iniciar
* O menu principal não é exibido
* Serviços aparecem como ativos, mas não podem ser encerrados
* Tunnels falham ao iniciar sem erro claro

Este deve ser sempre o **primeiro passo de diagnóstico**.

---

## ❌ Quando NÃO Abrir uma Issue Ainda

Não abra uma issue no GitHub se o problema for resolvido após executar o reset acima.

Isso ajuda a manter o repositório organizado e focado em problemas reais.

---

## 🐞 Quando Abrir uma Issue

Se o problema **persistir mesmo após o reset**, abra uma issue e inclua:

* Sistema operacional
* Versão do Python
* Mensagens de erro ou stack trace
* Passos para reproduzir o problema

Essas informações aceleram a análise e a correção.

---

## 🛡️ Nota de Segurança dos Dados

Este procedimento **não**:

* Remove binários de tunnels
* Remove provedores baixados
* Altera configurações do sistema

Ele apenas limpa o estado interno do AutoTunnel.

---

## 📌 Recomendação Final

Sempre execute este procedimento de reset **antes de solicitar suporte**.

Ele resolve a grande maioria dos problemas de inicialização.

---

Happy tunneling 🚀
