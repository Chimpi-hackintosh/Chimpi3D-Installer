# Chimpi3D 🐒

Editor 3D experimental para Windows, macOS e Linux

## Baixar os aplicativos

**[Releases: Windows, Linux e macOS](https://github.com/Chimpi-hackintosh/Chimpi3D-Installer/releases)**

Cada Release completo contem os **quatro** aplicativos compilados:

- Windows: `Chimpi3D.exe`
- Linux x86_64: `Chimpi3D-Linux-x86_64.tar.gz`, que inclui a pasta do aplicativo e bibliotecas
- macOS Intel: `Chimpi3D-macOS-Intel.app.zip`
- macOS Apple Silicon (M1/M2/M3/M4): `Chimpi3D-macOS-AppleSilicon.app.zip`

**Publicacao:** o workflow **Publicar Chimpi3D no Release** compila todos os sistemas e cria automaticamente um novo Release para cada atualizacao relevante da branch `main`. So publica se os quatro pacotes forem gerados. Tambem pode ser iniciado pela aba Actions > Publicar Chimpi3D no Release > Run workflow

Os workflows separados **Windows EXE**, **Linux Executable** e **macOS APP** continuam disponiveis em Actions para compilar um sistema individualmente. Seus resultados ficam em Artifacts, nao no Release

## Funcionalidades

- Criar cubos, esferas, cones e cilindros, mover, duplicar e redimensionar
- Importar/exportar OBJ e STL e importar PLY
- Transformar PNG em relevo 3D simplificado
- Salvar e abrir projetos `.chimpi3d`
- Gerar formas simples por descricao, offline ou com Ollama local opcional (`llama3.2:1b` instalado separadamente)
- Abrir Thingiverse no navegador para explorar e baixar modelos
- Enviar G-code feito em um slicer a servidores OctoPrint ou Moonraker compativeis, sem iniciar impressao

O projeto ainda nao e um clone completo do Blender nem oferece conexao universal a todas as impressoras 3D. Os aplicativos macOS nao sao assinados ou notarizados pela Apple

## Rodar o codigo-fonte

Com Python 3.11: `pip install -r requirements.txt` e `python main.py`

Os workflows comprovam que os pacotes foram criados, mas nao substituem testes da interface grafica em cada computador
