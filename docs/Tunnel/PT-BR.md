# Adicionando Novos Provedores de Tunnel

Este documento explica, de forma **detalhada**, como criar e integrar novos provedores de tunnel no **AutoTunnel** utilizando o sistema de plugins embutido.

O objetivo da arquitetura é tornar os provedores de tunnel **isolados, portáteis, auto-descobertos e fáceis de estender**, sem a necessidade de modificar o núcleo da aplicação.

---

## 🧠 Visão Geral da Arquitetura

O AutoTunnel utiliza um **sistema de tunnels baseado em plugins**.

* Cada provedor de tunnel vive em seu próprio arquivo Python
* Os provedores são descobertos dinamicamente em tempo de execução
* A aplicação principal não possui lógica fixa de provedores
* Todos os provedores seguem a mesma interface mínima

Isso permite:

* Fácil extensão
* Separação clara de responsabilidades
* Manutenção independente por provedor

---

## 📁 Estrutura de Diretórios

Todos os provedores de tunnel devem ficar dentro do diretório `tunnels/`:

```
AutoTunnel/
├── AutoTunnel.py
├── tunnels/
│   ├── Cloudflared.py
│   ├── Ngrok.py
│   └── SeuTunnel.py   ← novo provedor
```

O nome do arquivo **não é relevante**, desde que termine com `.py`.

---

## 🔍 Descoberta Automática de Provedores

Ao iniciar, o AutoTunnel:

1. Varre o diretório `tunnels/`
2. Importa todos os arquivos `.py`
3. Procura por uma classe chamada `TunnelPlugin`
4. Instancia a classe encontrada
5. Registra o provedor internamente

Se qualquer uma dessas etapas falhar, o provedor é ignorado silenciosamente para não comprometer a execução da ferramenta.

---

## 🧩 Classe Obrigatória: `TunnelPlugin`

Todo provedor **deve** expor uma classe chamada:

```
TunnelPlugin
```

Essa classe é o contrato entre o provedor e o AutoTunnel.

---

## ✅ Métodos Obrigatórios

A classe `TunnelPlugin` **precisa** implementar os métodos abaixo.

### `name(self) -> str`

Retorna o nome do provedor de tunnel que será exibido.

Usado para:

* Listagem no menu
* Logs
* Controle de estado

Exemplo:

```
def name(self):
    return "MeuTunnel"
```

---

### `installed(self) -> bool`

Verifica se o binário do provedor já está disponível no sistema.

Responsabilidades:

* Verificar a existência do binário
* Retornar `True` se estiver utilizável
* Retornar `False` se a instalação for necessária

Exemplo:

```
def installed(self):
    return os.path.exists(self.binary_path)
```

---

### `install(self) -> None`

Responsável por instalar o provedor automaticamente.

Diretrizes:

* Deve ser **totalmente automático**
* Não deve exigir interação do usuário
* Deve instalar nos diretórios portáteis do AutoTunnel
* Deve lançar exceções em caso de falha

Tarefas comuns:

* Download do binário
* Aplicar permissões de execução
* Validação da instalação

---

### `start(self, port: int) -> str`

Inicia o tunnel e expõe uma porta local.

Parâmetros:

* `port`: porta local do servidor HTTP

Responsabilidades:

* Criar o processo do tunnel
* Capturar stdout/stderr quando necessário
* Extrair a URL pública
* Armazenar o PID do processo

Deve retornar:

* A URL pública do tunnel como string

Exemplo:

```
def start(self, port):
    self.process = subprocess.Popen([...])
    return public_url
```

---

### `stop(self) -> None`

Encerra o tunnel em execução.

Responsabilidades:

* Finalizar o processo do tunnel
* Limpar arquivos temporários, se necessário
* Falhar de forma graciosa caso já esteja parado

Exemplo:

```
def stop(self):
    if self.process:
        self.process.terminate()
```

---

## 📦 Métodos Opcionais

### `description(self) -> str`

Retorna uma descrição curta e legível do provedor.

Utilizado em menus e painéis informativos.

---

### `requires_auth(self) -> bool`

Indica se o provedor exige autenticação (token, conta, etc.).

Se retornar `True`, o AutoTunnel automaticamente:

* Solicitará as credenciais ao usuário
* Armazenará de forma segura no arquivo de configuração

---

### `configure(self, config: dict) -> None`

Permite lógica de configuração personalizada para provedores avançados.

Útil para:

* Tokens
* Regiões
* Domínios personalizados

---

## 🔐 Configuração e Armazenamento

Os provedores **não devem** usar caminhos absolutos fixos.

Utilize sempre os diretórios portáteis do AutoTunnel:

* Configuração: `~/.config/autotunnel/`
* Dados: `~/.local/share/autotunnel/`

Todos os dados específicos do provedor devem ficar em um subdiretório próprio:

```
~/.local/share/autotunnel/meutunnel/
```

---

## 📝 Regras de Log

Os provedores devem:

* Registrar eventos importantes (início, parada, erros)
* Evitar verbosidade excessiva
* Nunca registrar tokens, segredos ou credenciais

Os logs são capturados automaticamente pelo AutoTunnel sempre que possível.

---

## ❌ O Que NÃO Fazer

* NÃO modificar o arquivo `AutoTunnel.py`
* NÃO usar caminhos absolutos fixos
* NÃO usar `input()` dentro do plugin
* NÃO exigir instalação manual
* NÃO encerrar a aplicação em caso de erro — falhe de forma controlada

---

## 🧪 Testando Seu Provedor

Antes de utilizar ou submeter um novo provedor:

1. Remova binários existentes
2. Inicie o AutoTunnel
3. Selecione seu provedor
4. Verifique a instalação automática
5. Inicie o tunnel
6. Encerre o tunnel
7. Reinicie o AutoTunnel e teste novamente

O provedor deve funcionar corretamente mesmo após reinicializações.

---

## 📌 Provedores de Referência

Use os provedores já existentes como base:

* `tunnels/Cloudflared.py`
* `tunnels/Ngrok.py`

Eles demonstram:

* Instalação automática
* Gerenciamento de processos
* Extração de URL pública
* Tratamento de erros

---

## 🚀 Diretrizes de Contribuição

Ao contribuir com um novo provedor:

* Siga este documento rigorosamente
* Mantenha o código limpo e legível
* Comente trechos não triviais
* Teste em um ambiente limpo

