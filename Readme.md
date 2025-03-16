# Setup instructions

* create a venv (somehow, I forgot how)
* pip install poetry
* eval `poetry env activate
* poetry install

install postgresql

```bash
sudo apt install postgresql
```

Set the local net to trust by editing

```bash
sudo nvim /etc/postgresql/16/main/pg_hba.conf
```

Create a superuser account as your user

```bash
sudo -u postgres createuse --superuser $USER
```

activate venv

```bash
source .venv/bin/activate
```

create the database:

```bash
createdb chatdb
```

Set the DATABASE_URL

```bash
export DATABASE_URL="postgresql+psycopg2://$USER@localhost:5433/chatdb"
```

Then run the app with:

```bash
python main.py
```
