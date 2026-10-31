# Chimpi3D 🐒

Editor 3D experimental para Windows, macOS e Linux

## Funcionalidades

- Criar cubos, esferas, cones e cilindros, mover, duplicar e redimensionar
- Importar/exportar OBJ e STL e importar PLY
- Transformar PNG em relevo 3D simplificado
- Salvar e abrir projetos `.chimpi3d`
- Gerar formas simples por descrição, offline ou com Ollama local opcional (`llama3.2:1b` instalado separadamente)
- Abrir Thingiverse no navegador para explorar e baixar modelos
- Enviar G-code feito em um slicer a servidores OctoPrint ou Moonraker compatíveis, sem iniciar impressão

Este não é um clone completo do Blender e não conecta automaticamente a toda impressora 3D

## Compilação

Na aba **Actions**, escolha `Windows EXE`, `Linux Executable` ou `macOS APP`, clique **Run workflow** e baixe o resultado em **Artifacts**

Windows: `Chimpi3D.exe`

Linux: `Chimpi3D-Linux-x86_64.tar.gz`

macOS Intel: `Chimpi3D-macOS-Intel.app.zip` (não assinado)

## Código-fonte

Com Python 3.11: `pip install -r requirements.txt` e `python main.py`

Versão inicial no GitHub, builds e interface gráfica ainda precisam de validação nos sistemas de destino
