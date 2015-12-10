#!/bin/sh
# sh yahooscraper.sh 

if [ -z "$1" ]
then
	echo "ERROR you must enter one arg related to the Yahoo URL DB use -h for Help"
else
	if [ "$1" = "-h" ]
	then
		echo "This script need the name of the database containing question URLs"
		echo "- sh yahooscraper.sh <dbname> "
	else
	echo "Reading from $1 database "
	cd yahooscraper/yahooscraper/yahooscraper/spiders
	scrapy crawl yahoo -o question-and-answer-report.json -a database_name=$1
	fi
fi