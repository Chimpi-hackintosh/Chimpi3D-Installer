# Chimpi3D 🐒

Editor 3D experimental para Windows, macOS e Linux

## Baixar os aplicativos

**[Releases: Windows, Linux e macOS](https://github.com/Chimpi-hackintosh/Chimpi3D-Installer/releases)**

Cada versão publicada em Releases contém os **quatro** aplicativos compilados:

- **Windows:** `Chimpi3D.exe`
- **Linux x86_64:** `Chimpi3D-Linux-x86_64.tar.gz`, que inclui a pasta do aplicativo e suas bibliotecas
- **macOS Intel:** `Chimpi3D-macOS-Intel.app.zip`
- **macOS Apple Silicon:** `Chimpi3D-macOS-AppleSilicon.app.zip`

**Publicação automática:** o workflow **Publicar Chimpi3D nos Releases** compila todos os sistemas e cria uma versão no GitHub Releases a cada atualização relevante da branch `main`. A publicação só acontece se todos os quatro pacotes forem gerados com sucesso

Também é possível executá-lo manualmente em **Actions → Publicar Chimpi3D nos Releases → Run workflow**

Os workflows **Windows • Executável**, **Linux • Executável** e **macOS • Aplicativo** continuam disponíveis em Actions para compilar um sistema individualmente. Esses resultados ficam em **Artifacts**, não em Releases

## Funcionalidades

- Criar cubos, esferas, cones e cilindros, além de mover, duplicar e redimensionar objetos
- Importar e exportar OBJ e STL, além de importar PLY
- Transformar imagens PNG em relevos 3D simplificados
- Salvar e abrir projetos `.chimpi3d`
- Gerar formas simples por descrição, offline ou com Ollama local opcional (`llama3.2:1b`, instalado separadamente)
- Abrir o Thingiverse no navegador para explorar e baixar modelos
- Enviar G-code criado em um fatiador (slicer) para servidores OctoPrint ou Moonraker compatíveis, sem iniciar a impressão

O projeto ainda não é um clone completo do Blender e não oferece conexão universal a todas as impressoras 3D

Os aplicativos macOS não possuem assinatura digital nem notarização da Apple

## Executar o código-fonte

Com Python 3.11:

```bash
pip install -r requirements.txt
python main.py
```

Os workflows verificam a criação dos pacotes, mas isso não substitui os testes da interface gráfica em computadores reais
