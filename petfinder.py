import mechanize
import pickledb
import traceback
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

mail_conf = pickledb.load("./mail_conf.db", False)
ohs_site_root = "https://www.oregonhumane.org"
ohs_search_page = ohs_site_root + "/adopt/?type=dogs"
ohs_adopt_page = ohs_site_root + "/adoption-questionnaire/"
old_ohs_dogs = pickledb.load("./ohs_dogs.db", True)
swh_site_root = "https://southwesthumane.org"
swh_search_page = swh_site_root + "/adopt/dogs/"
swh_adopt_page = swh_site_root + "/adopt/"
old_swh_dogs = pickledb.load("./swh_dogs.db", True)

# Browser
br = mechanize.Browser()
br.set_handle_equiv(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
br.addheaders = [('User-agent', 'Chrome')]

def ohs_petfind():
    ohs = br.open(ohs_search_page)
    ohs_soup = BeautifulSoup(ohs, features="html5lib")
    ohs_dogs = ohs_soup.find_all(attrs={"data-ohssb-type": "dog"})
    
    old_dogs = []
    new_tricks = []

    for dog in ohs_dogs:
        dog_id = dog.find(class_ = "id").string
        if not dog_id in old_ohs_dogs.get("old_dogs"):
            dog_friend = {
                "img": dog.img, 
                "info_link": ohs_site_root + dog.a.get("href"),
                "name": dog.find(class_ = "name").string,
                "id": dog_id,
                "breed": dog.find(class_ = "breed").string,
                "sex": dog.find(class_ = "sex").string,
                "color": dog.find(class_ = "color").string,
                "age": dog.find(class_ = "age").string,
                "weight": dog.find(class_ = "weight").string
            }

            dog_friend["img"].attrs["height"] = 175
            dog_friend["img"].attrs["width"] = 233
            dog_friend["adopt_link"] = (
                ohs_adopt_page + 
                "?animal_id=" + 
                dog_friend["id"] + 
                "&animal_name=" + 
                dog_friend["name"])

            # TODO: Prefill form
            dog_friend["adopt_form"] = f"""<form action={dog_friend["adopt_link"]} method="post" style="text-align:center;">
                <input type="hidden" name="foo" value="bar" />
                <input type="submit" value="Give Me That Floof" />
            </form>"""

            new_tricks.append(dog_friend)

        old_dogs.append(dog_id)

    old_ohs_dogs.set("old_dogs", old_dogs)
    return new_tricks

def swh_petfind():
    swh = br.open(swh_search_page)
    swh_soup = BeautifulSoup(swh, features="html5lib")
    swh_dogs = swh_soup.find_all(class_ = "box animal")
    
    old_dogs = []
    new_tricks = []

    for dog in swh_dogs:
        dog_stats = dog.find_all("li")
        dog_info = dog.a.attrs["href"]
        dog_id = dog_info.split("=")[1]

        if not dog_id in old_swh_dogs.get("old_dogs"):
            dog_friend = {
                "img": dog.img,
                "info_link": swh_site_root + dog_info,
                "adopt_link": swh_adopt_page,
                "name": dog.h3.string,
                "id": dog_id,
                "breed": dog_stats[0].string,
                "sex": dog_stats[1].string,
                "age": dog_stats[2].string
            }

            dog_friend["img"].attrs["src"] = dog_friend["img"].attrs["data-src"]
            dog_friend["img"].attrs["height"] = 215
            dog_friend["img"].attrs["width"] = 233

            # TODO: Prefill form
            dog_friend["adopt_form"] = f"""<form action={dog_friend["adopt_link"]} method="post" style="text-align:center;">
                <input type="hidden" name="foo" value="bar" />
                <input type="submit" value="Give Me That Floof" />
            </form>"""

            new_tricks.append(dog_friend)

        old_dogs.append(dog_id)

    old_swh_dogs.set("old_dogs", old_dogs)
    return new_tricks

def petmail(dogs):
    fromaddr = mail_conf["floof_alert"]["from"]
    toaddr = mail_conf["floof_alert"]["to"]
    password = mail_conf["floof_alert"]["password"]

    # Login to the server
    server = SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(fromaddr, password)

    # Build the message
    message = MIMEMultipart("alternative")
    message["Subject"] = mail_conf["floof_alert"]["subject"]
    message["To"] = toaddr
    message["From"] = fromaddr
    
    body = """<html>
        <head>
        </head>
        <body>"""

    dog_div = ("<div style = \""
                "display: inline-block; "
                "max-width: 233px; "
                "padding: .625em; "
                "margin-right: 1.75em; "
                "margin-bottom: 1.25em;"
                "border: 1px solid #aeb0b3;"
                "border-radius: .3125em;\">")

    for dog in dogs:
        body += dog_div
        body += str(dog["img"])
        body += "</a><br /><div style = \"overflow:hidden;white-space:nowrap\">"
        body += "<strong>" + dog["name"] + "</strong> - " + dog["id"] + "<br />"
        body += dog["breed"] + "<br />"
        body += dog["sex"] + "<br />"
        body += dog["age"] + "<br />"
        if("color" in dog):
            body += dog["color"] + "<br />"
            body += dog["weight"] + "<br />"
        body += "<a href=\"" + dog["info_link"] + "\">More Info</a><br /><hr />"
        body += dog["adopt_form"]
        body += "</div></div>"

    body += "</body></html>"

    message.attach(MIMEText(body, "html"))
    server.sendmail(fromaddr, toaddr, message.as_string())
    server.close()

def troublemail(exception):
    fromaddr = mail_conf["error_msg"]["from"]
    toaddr = mail_conf["error_msg"]["to"]
    password = mail_conf["error_msg"]["password"]

    # Login to the server
    server = SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(fromaddr, password)

    # Build the message
    message = "\r\n".join(["From: " + fromaddr, "To: " + toaddr, "Subject: " + mail_conf["error_msg"]["subject"], ""])
    message += "\r\n"
    message += "Encountered exception searching for dogs, sir!"
    message += "\r\n\r\n"
    message += exception

    server.sendmail(fromaddr, toaddr, message)
    server.close()


if __name__ == "__main__":
    try:
        ohs_dogfriends = ohs_petfind()
        swh_dogfriends = swh_petfind()
        if ohs_dogfriends or swh_dogfriends:
            petmail(ohs_dogfriends + swh_dogfriends)
    except:
        troublemail(traceback.format_exc())