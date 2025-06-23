# PACS

Sistema PACS (Picture Archiving and Communication System) simplificado desenvolvido em Django.

## Requisitos

- Python 3.8 ou superior
- Windows 10
- Visual Studio Code

## Instalação

1. Clone este repositório
2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
```bash
# Windows
venv\Scripts\activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Execute as migrações:
```bash
python manage.py migrate
```

6. Crie um superusuário:
```bash
python manage.py createsuperuser
```

7. Execute o servidor:
```bash
python manage.py runserver
```

## Funcionalidades

- Login de usuários
- Upload de arquivos DICOM
- Visualização de imagens DICOM
- Armazenamento de arquivos DICOM
- Exclusão de arquivos DICOM 
