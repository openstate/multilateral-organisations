# Open Multilaterals
Visualization showing how countries perform in getting contracts from multilateral organizations.


## Requirements
[Docker Compose](https://docs.docker.com/compose/install/)

## Run
- Clone or download this project from GitHub:
- Copy `docker/docker-compose.yml.example` to `docker/docker-compose.yml` and edit it
   - Fill in a password at `<DB_PASSWORD>`
- Copy `config.py.example` to `config.py` and edit it
   - Create a SECRET_KEY as per the instructions in the file
   - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
   - Specify email related information in order for the application to send emails
- Production
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `sudo docker-compose up -d`
   - Compile the assets, see the section below
   - Set up backups
      - Copy `docker/backup.sh.example` to `docker/backup.sh` and edit it
         - Fill in the same `<DB_PASSWORD>` as used in `docker/docker-compose.yml`
      - To run manually use `sudo ./backup.sh`
      - To set a daily cronjob at 03:46
         - `sudo crontab -e` and add the following line (change the path below to your `multilateral-organisations/docker` directory path)
         - `46 3 * * * (cd <PATH_TO_multilateral-organisations/docker> && sudo ./backup.sh)`
      - The resulting SQL backup files are saved in `docker/docker-entrypoint-initdb.d`
- Development; Flask debug will be turned on which automatically reloads any changes made to Flask files so you don't have to restart the whole application manually
   - Make sure to extract the latest MySQL backup in `docker/docker-entrypoint-initdb.d` if you want to import it: `gunzip latest-mysqldump-daily.sql.gz`
   - `cd docker`
   - `docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Compile the assets, see the section below
   - Retrieve the IP address of the nginx container `docker inspect mlo_nginx_1` and add it to your hosts file `/etc/hosts`: `<IP_address> open-multilaterals.org`
- Useful commands
   - Remove and rebuild everything (this also removes the MySQL volume containing all records (this is required if you want to load the .sql files from `docker/docker-entrypoint-initdb.d` again))
      - Production: `docker-compose down --rmi all && docker volume rm mlo_mlo-mysql-volume && docker-compose up -d`
      - Development: `docker-compose -f docker-compose.yml -f docker-compose-dev.yml down --rmi all && docker volume rm mlo_mlo-mysql-volume && docker-compose -f docker-compose.yml -f docker-compose-dev.yml up -d`
   - Reload Nginx: `sudo docker exec mlo_nginx_1 nginx -s reload`
   - Reload uWSGI (only for production as development environment doesn't use uWSGI and automatically reloads changes): `sudo touch uwsgi-touch-reload`

## Compile assets
All the following commands have to be run in the `mlo_nodejs_1` container, so first enter it using:
- `sudo docker exec -it mlo_nodejs_1 bash`

Run the following commands once after a new install:
- `npm install -g gulp bower`
- `npm install`
- `bower install --allow-root`

To compile the assets:
- `gulp`

To automatically compile the assets in development on any file changes (always run `gulp` first to compile any changes up till now):
- `gulp watch`

## CLI
To access the CLI of the app run `sudo docker exec -it mlo_app_1 bash` and run `flask`. Here are the CLI commands to load all data into the database (this might take some minutes):

- `flask mlo load-records --csv-file files/NATO.csv`
- `flask mlo load-records --csv-file files/UN.csv`
- `flask mlo load-records --csv-file files/World_Bank_major_contract_awards.csv`
- `flask mlo load-records --csv-file files/World_Bank_corporate_procurement_contract_awards.csv`

## To enter the MySQL database
- `sudo docker exec -it mlo_mysql_1 bash`
- `mysql -p`
- Retrieve database password from `docker/docker-compose.yml` and enter it in the prompt

## Update the data
- See the `data` folder for instructions on how to update the datasets
