# UniFlow
cs50_Final_Project


## Setup and Run (Local Developement)

To run **UniFlow** locally:

### 1. Clone the repository

```bash
git clone https://github.com/andrewkm05/UniFlow.git
cd UniFlow
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies 

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
flask run --debug
```

<br>

### Notes:

- Always activate the virtual environment before working:

```bash
source .ven/bin/activate
```

- To update dependencies after adding a new library:

```bash
pip freeze > requirements.txt
```

- Flask auto-reloads changes when `--debug` mode is on