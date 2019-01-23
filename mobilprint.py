#!/usr/bin/env python3

import requests
from html.parser import HTMLParser


class PrintJobExtractor(HTMLParser):

    # Storing extracted state
    state = {"JID": None, "PID": None, "PageTo": None}

    def attr_store_value(self, key, attrs):
        for (k, v) in attrs:
            if k == "value":
                self.state[key] = v

    def get_print_job_state(self):
        return self.state["JID"], self.state["PID"], self.state["PageTo"]

    def handle_starttag(self, tag, attrs):
        if tag != "input":
            return

        if ("name", "JID") in attrs:
            self.attr_store_value("JID", attrs)
        elif ("name", "PID") in attrs:
            self.attr_store_value("PID", attrs)
        elif ("name", "PageTo") in attrs:
            self.attr_store_value("PageTo", attrs)


def login(username, password):
    login_info = {"LoginAction": "login", "Username": username,
                  "Password": password}
    return requests.post("https://mobilprint.uit.no/login.cfm",
                         data=login_info).history[0].cookies


def upload_file(filename, cookies):
    file = {"FileToPrint": open(filename, "rb")}
    form_data = {"type": "file"}
    return requests.post("https://mobilprint.uit.no/webprint.cfm",
                         data=form_data, files=file, cookies=cookies)


def get_print_job_details(html, cookies):
    extractor = PrintJobExtractor()
    extractor.feed(html)
    jid, pid, page_to = extractor.get_print_job_state()

    print(".", end="", flush=True)
    while jid is None and pid is None:
        res = requests.get("https://mobilprint.uit.no/index.cfm",
                           cookies=cookies)
        extractor.feed(res.text)
        jid, pid, page_to = extractor.get_print_job_state()
        print(".", end="")
    return jid, pid, page_to


def print_job(jid, pid, page_to, cookies):
        form_data = {"JID": jid, "PID": pid, "NumberOfCopies": 1,
                     "PageFrom": 1, "PageTo": page_to, "Duplex": 2,
                     "method": "printjob"}
        return requests.post("https://mobilprint.uit.no/afunctions.cfm",
                             data=form_data, cookies=cookies)


if __name__ == "__main__":
    import sys
    import getpass
    if len(sys.argv) < 3:
        print("Usage: {} <username> <file>".format(sys.argv[0]))
        sys.exit()

    username = sys.argv[1]
    filename = sys.argv[2]
    password = getpass.getpass()

    print("Sending to printer", end="", flush=True)
    cookie = login(username, password)
    status_page = upload_file(filename, cookie)
    jid, pid, page_to = get_print_job_details(status_page.text, cookie)
    print_job(jid, pid, page_to, cookie)
    print("done", flush=True)
