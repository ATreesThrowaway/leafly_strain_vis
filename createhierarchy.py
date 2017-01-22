#!/usr/bin/env python3

import os
import sys
import json
import copy


MINRATINGS = 1000


class Strain:
    def __init__(self, data, data_index):
        data_strain = data[data_index]
        self.data = data;
        self.data_index = data_index;
        self.num_index = 0;

        self.name = data_strain["Name"]
        self.symbol = data_strain["Symbol"]
        self.category = data_strain["Category"]
        self.url = "https://www.leafly.com/{}/{}".format(data_strain["Category"], data_strain["UrlName"])
        self.ratings = data_strain["RatingCount"]
        self.level = -1
        self.toplevel = False
        self.bottomlevel = True
        self.descendants = []
        self.children = []
        self.parents = []

    def __str__(self):
        return "[{:3}]  {}  {:25}  {:3} <-  {:3} ->  {:3} -->".format(self.symbol, self.category[0], self.name,
                len(self.parents), len(self.children), len(self.descendants))

    @property
    def colour(self):
        colours = {"Sativa": "#d44727",
                "Indica": "#6e335e",
                "Hybrid": "#76bd1d"}
        return colours[self.category]

    def find_relatives(self, strains):
        data_parents = self.data[self.data_index]["Parents"]
        for data_parent in data_parents:
            for s in strains:
                if s == self:
                    continue
                if data_parent["StrainId"] != s.data[s.data_index]["Id"]:
                    continue
                p = s
                break
            else:
                continue
            self.parents.append(p)
            p.children.append(self)
            p.bottomlevel = False
        self.toplevel = len(self.parents) == 0

    def cleanup_tree(self, ancestors=[]):
        ancestors.append(self)

        # Get rid of hierarchial cycles
        for c in self.children:
            for a in ancestors:
                if a in c.children:
                    c.children.remove(a)
            c.cleanup_tree(ancestors)

        ancestors.remove(self)

        # Get rid cycles within children
        for c1 in self.children:
            for c2 in self.children:
                if c1 not in c2.children or c2 not in c1.children:
                    continue
                if c1.ratings > c2.ratings:
                    c1.parents.remove(c2)
                    c2.children.remove(c1)
                else:
                    c2.parents.remove(c1)
                    c1.children.remove(c2)

    def calculate_descendants(self):
        self.descendants = []
        for c in self.children:
            self.descendants += c.calculate_descendants() + [c]
        self.descendants = list(set(self.descendants))
        return self.descendants


def main(args):
    strains = []

    # Load data
    with open("strains.json", "r") as f:
        data = json.load(f)
        for i in range(len(data)):
            strains.append(Strain(data, i))

    # Build family structure
    for s in strains:
        s.find_relatives(strains)

    # Get rid of cycles to avoid trouble later on
    for s in strains:
        s.cleanup_tree()

    # Filter out irrelevant strains
    deleted = 1
    while deleted > 0:
        deleted = 0
        i = 0
        while i < len(strains):
            s = strains[i]
            if not s.bottomlevel or s.ratings > MINRATINGS:
                i += 1
                continue
            deleted += 1
            for p in s.parents:
                p.children.remove(s)
                if len(p.children) == 0:
                    p.bottomlevel = True
            strains.pop(i)

    # Remove singular strains
    #i = 0
    #while i < len(strains):
    #    if strains[i].toplevel and len(strains[i].children) == 0:
    #        strains.pop(i)
    #    else:
    #        i += 1

    print(len(strains))

    # Calculate total descendants of each strain
    for s in strains:
        s.calculate_descendants()

    # Format data
    data_nodes = []
    for s in strains:
        s.num_index = len(data_nodes)
        data_nodes.append({
            "id": s.num_index,
            "label": s.symbol,
            "title": s.name,
            "color": s.colour,
            "url": s.url,
            "value": s.ratings,
            "mass": len(s.descendants) + 1})

    data_edges = []
    for s in strains:
        for c in s.children:
            data_edges.append({
                "from": s.num_index,
                "to": c.num_index})

    with open("data.js", "w") as f:
        f.write("data_nodes = [\n")
        for n in data_nodes:
            f.write("    " + json.dumps(n) + ",\n")
        f.write("];\n\ndata_edges = [\n")
        for e in data_edges:
            f.write("    " + json.dumps(e) + ",\n")
        f.write("];\n")
    

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
