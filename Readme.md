# Setup instructions

* create a venv (somehow, I forgot how)
* pip install poetry
* eval `poetry env activate
* poetry install

install postgressql
sudo apt install postgres

Set the local net to trust by editing
sudo nvim /etc/postgresql/16/main/pg_hba.conf

Create a superuser account as your user
sudo -u postgres createuse --superuser $USER

activate venv
source .venv/bin/activate

create the database:

createdb chatdb

Set the DATABASE_URL
export DATABASE_URL="postgresql+psycopg2://$USER@localhost:5433/chatdb"

Then run the app with:
python main.py
