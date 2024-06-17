if [[ -d y2mate-bot ]]; then
  rm y2mate-bot -rf

fi

git clone https://github.com/Simatwa/y2mate-bot.git
cp .env y2mate-bot/
cd y2mate-bot
pip install -U pip
pip install -r requirements.txt
export https_proxy="199.167.236.12:3128"
python main.py