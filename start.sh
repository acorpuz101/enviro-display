PROJECT_DIR=/home/pi/display-app
exec python $PROJECT_DIR/display-enviro.py >> $PROJECT_DIR/logs.log &
echo "kill -9 $!" > $PROJECT_DIR/shutdown.sh
