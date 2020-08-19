# OHS / SWH Adoption Watchdog
Quick and dirty script to scrape the OHS and SWH websites and see if there are any new dogs listed for adoption.

`python3 pip install -r requirements.txt`  
`python3 petfinder.py`

For best results, stick it in a cronjob.

Whichever account is configured in mail_conf must have access from "less secure" applications enabled, since this is just using smtplib. 
