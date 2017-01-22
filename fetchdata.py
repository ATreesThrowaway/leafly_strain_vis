#!/usr/bin/env python3

import os
import sys
import json
import time

import requests


MAXRETRIES = 5
MAXPAGES = 200


def get(url):
    for i in range(MAXRETRIES):
        try:
            r = requests.get(url, headers={"Accept": "application/json, */*"})
            if r.status_code == 404:
                return None
            r.json()
        except Exception as e:
            print(str(e))
        else:
            return r

        time.sleep(3 ** i)

    print("\nMAXRETRIES exceeded, aborting")
    sys.exit(1)


def main(args):
    strains = []

    for i in range(1, MAXPAGES):
        print("Fetching page {} ...".format(i))

        r = get("https://www.leafly.com/explore/category-hybrid,indica,sativa/page-{}/sort-alpha".format(i))
        if r is None:
            print("\nDone.")
            break
            
        slist = r.json()["Model"]["Strains"]
        if len(slist) == 0:
            print("\nDone.")
            break

        for s in slist:
            print("    Fetching info on {} ... ".format(s["Name"]), end="")
            sys.stdout.flush()
            r = get("https://www.leafly.com/{}/{}".format(s["Category"], s["UrlName"]))
            if r is None:
                print("skipping.")
                continue
            else:
                print("done.")
            strains.append(r.json()["Model"]["Strain"])
    else:
        print("\nMAXPAGES reached, aborting.")
        return 1

    with open("strains.json", "w") as f:
        json.dump(strains, f)
        f.write("\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
