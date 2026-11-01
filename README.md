# Chimpi3D 0.3.0 🐒

Aplicativo experimental de modelagem 3D para Windows, Linux e macOS, com importação OBJ/STL, relevo a partir de PNG, biblioteca externa do Thingiverse e ChimpiAI (Ollama local opcional)

## 📦 Aplicativos e instaladores

**[Baixar todos os aplicativos no GitHub Releases](https://github.com/Chimpi-hackintosh/Chimpi3D-Installer/releases)**

Os Releases da versão **0.3.x** são montados automaticamente pelo GitHub Actions e incluem:

| Sistema | Arquivo | Formato |
|---|---|---|
| Windows | `Chimpi3D.exe` | Executável portátil |
| Windows 11 | `Chimpi3D-Setup-Windows.exe` | Instalador **NSIS** por usuário, com `of.exe` |
| Linux x86_64 | `Chimpi3D-Linux-x86_64.tar.gz` | Pasta executável e comando `of` |
| macOS Intel | `Chimpi3D-macOS-Intel.app.zip` | `.app` e comando `of` |
| macOS Apple Silicon | `Chimpi3D-macOS-AppleSilicon.app.zip` | `.app` e comando `of` |
| Todos | `SHA256SUMS.txt` | Verificação dos arquivos publicados |

O workflow **Publicar Chimpi3D nos Releases** só publica depois que **todos** os builds e a criação do instalador NSIS terminarem corretamente

## 🧊 Novo quadrado estilo UICorner

Use **Adicionar Quadrado UICorner** para criar uma peça 3D com os cantos arredondados, inspirada na propriedade `UICorner` do Roblox Studio

É uma **malha 3D própria**, não um objeto de interface do Roblox, com exportação OBJ/STL

## 📲 NFC opcional e código NFC300

- As TAGs NFC são **virtuais**, isto é, metadados que podem ser associados aos objetos do projeto
- Não é necessário associar NFC a nenhum modelo para continuar modelando ou exportando
- Clique em **Resgatar código NFC** e informe `NFC300` para adicionar **300 TAGs virtuais** à carteira local
- O código é resgatável **uma vez por instalação/perfil local**
- Escolha um objeto, clique em **Vincular TAG ao objeto**, ou remova a TAG quando quiser
- Clique em **Exportar TAGs (.json)** para exportar os identificadores virtuais
- TAGs vinculadas são salvas no projeto `.chimpi3d`

**Importante:** o Chimpi3D ainda **não** lê, grava nem entrega chips NFC físicos. O código não cria 300 etiquetas NFC reais, não é saldo de uma conta online e não representa uma licença comercial ou crédito externo

## 💻 Comando de instalação `of my pc`

Com o **comando `of` previamente instalado e acessível no PATH**, os seguintes exemplos são reconhecidos:

**Windows 11 (instalador NSIS):**

```cmd
of my pc --os Windows --os-version 11-NT install Chimpi3D
```

**macOS (pacote original publicado):**

```sh
of my pc --os macOS --os-version 28-GoldenGate install Chimpi3D --original
```

**Linux Mint:**

```sh
of my pc --os Linux --edition Linux Mint install Chimpi3D
```

A instalação busca **automaticamente** o aplicativo no GitHub Releases oficial, confere o arquivo com **SHA-256** e o instala, sem que a pessoa tenha que baixar o pacote manualmente. A conexão com a internet é necessária

**Não existe instalação sem transferir os arquivos do programa**: a transferência acontece em segundo plano no comando, e o procedimento e a origem são informados ao usuário

**Primeira instalação do `of`:** no Windows, o instalador NSIS inclui e registra `of.exe` no PATH do usuário; abra um novo terminal após a instalação. No Linux e macOS, o executável `of` acompanha os arquivos distribuídos e precisa estar disponível no diretório `~/.local/bin` incluído no PATH para ser chamado somente por `of`

Os parâmetros `11-NT` e `28-GoldenGate` são **rótulos aceitos** pela ferramenta, não uma confirmação de compatibilidade dessas versões. O instalador identifica o sistema operacional real antes de instalar, e os pacotes macOS não são assinados ou notarizados pela Apple

## ✨ Outras funcionalidades

- Cubos, esferas, cilindros e cones
- Importar, editar e exportar modelos OBJ e STL
- Abrir e salvar projetos `.chimpi3d`
- Relevo 3D de imagens PNG
- ChimpiAI opcional por meio de Ollama local
- Thingiverse aberto no navegador
- Envio opcional de G-code para OctoPrint ou Moonraker sem iniciar impressão automaticamente

O Chimpi3D ainda não é um clone completo do Blender e não se conecta automaticamente a todas as impressoras 3D

## 🛠️ Desenvolvimento

Para executar o código em Python 3.11:

```sh
pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_v030.py' -v
python main.py
```

Os workflows verificam compilação e testes automatizados, mas não substituem testes gráficos reais nos três sistemas

## Aviso de suporte

Aviso traduzido, data de 04/11/2026, versões e limites de distribuição em [SUPPORT.md](SUPPORT.md)
