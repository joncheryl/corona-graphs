import numpy as np
import pandas as pd
from collections import defaultdict
from tqdm.auto import tqdm
import glob
import os
import fitz


def parse_stream(stream):
    data_raw = []
    data_transformed = []
    rotparams = None
    npatches = 0
    for line in stream.splitlines():
        if line.endswith(" cm"):
            # page 146 of https://www.adobe.com/content/dam/acom/en/devnet/
            # pdf/pdfs/pdf_reference_archives/PDFReference.pdf
            rotparams = list(map(float, line.split()[:-1]))
        elif line.endswith(" l"):
            x, y = list(map(float, line.split()[:2]))
            a, b, c, d, e, f = rotparams
            xp = a*x+c*y+e
            yp = b*x+d*y+f
            data_transformed.append([xp, yp])
            data_raw.append([x, y])
        elif line.endswith(" m"):
            npatches += 1
        else:
            pass
    data_raw = np.array(data_raw)
    basex, basey = data_raw[-1]
    good = False
    if basex == 0.:
        data_raw[:, 1] = basey - data_raw[:, 1]
        data_raw[:, 1] *= 100/60.
        data_raw = data_raw[data_raw[:, 1] != 0.]
        if npatches == 1:
            good = True
    return dict(data=np.array(data_raw), npatches=npatches, good=good)


def parse_page(doc, ipage, verbose=False):
    categories = [
        "Retail & recreation",
        "Grocery & pharmacy",
        "Parks",
        "Transit stations",
        "Workplace",
        "Residential",
    ]

    counties = []
    curr_county = None
    curr_category = None
    data = defaultdict(lambda: defaultdict(list))
    pagetext = doc.getPageText(ipage)
    lines = pagetext.splitlines()
    tickdates = list(filter(lambda x: len(x.split()) == 3, set(lines[-10:])))

    for line in lines:
        # don't need these lines at all
        if ("* Not enough data") in line:
            continue
        if ("needs a significant volume of data") in line:
            continue

        # if we encountered a category, add to dict, otherwise
        # push all seen lines into the existing dict entry
        if any(line.startswith(c) for c in categories):
            curr_category = line
        elif curr_category:
            data[curr_county][curr_category].append(line)

        # If it doesn't match anything, then it's a county name
        if (all(c not in line for c in categories)
            and ("compared to baseline" not in line)
            and ("Not enough data" not in line)):
            # saw both counties already
            if len(data.keys()) == 2:
                break
            # there's only one county on page
            if len(data.keys()) == 1 and "Sun Feb 23" in line:
                break
            counties.append(line)
            curr_county = line

    newdata = {}
    for county in data:
        newdata[county] = {}
        for category in data[county]:
            # if the category text ends with a space, then there was a
            # star/asterisk there indicating lack of data. we skip these.
            if category.endswith(" "):
                continue
            temp = [x for x in data[county][category] if
                    "compared to baseline" in x]
            if not temp:
                continue
            percent = int(temp[0].split()[0].replace("%", ""))
            newdata[county][category.strip()] = percent
    data = newdata

    tomatch = []
    for county in counties:
        for category in categories:
            if category in data[county]:
                tomatch.append([county, category, data[county][category]])

    if verbose:
        print(len(tomatch))
        print(data)

    goodplots = []
    xrefs = sorted(doc.getPageXObjectList(ipage),
                   key=lambda x: int(x[1].replace("X", "")))

    for i, xref in enumerate(xrefs):
        stream = doc.xrefStream(xref[0]).decode()
        info = parse_stream(stream)
        if not info["good"]:
            continue
        goodplots.append(info)
    if verbose:
        print(len(goodplots))

    ret = []

    if len(tomatch) != len(goodplots):
        return ret

    for m, g in zip(tomatch, goodplots):
        xs = g["data"][:, 0]
        ys = g["data"][:, 1]
        maxys = ys[np.where(xs == xs.max())[0]]
        maxy = maxys[np.argmax(np.abs(maxys))]

        # parsed the tick date labels as text. find the min/max (first/last)
        # and make evenly spaced dates, one per day, to assign to x values
        # between 0 and 200 (the width of the plots).
        ts = list(map(lambda x: pd.Timestamp(x.split(None, 1)[-1] + ", 2020"),
                      tickdates))
        low, high = min(ts), max(ts)
        dr = list(map(lambda x: str(x).split()[0], pd.date_range(low, high,
                                                                 freq="D")))
        lutpairs = list(zip(np.linspace(0, 200, len(dr)), dr))

        dates = []
        values = []
        asort = xs.argsort()
        xs = xs[asort]
        ys = ys[asort]
        for x, y in zip(xs, ys):
            date = min(lutpairs, key=lambda v: abs(v[0]-x))[1]
            dates.append(date)
            values.append(round(y, 3))

        ret.append(dict(
            county=m[0], category=m[1], change=m[2],
            values=values,
            dates=dates,
            changecalc=maxy,
        ))
    return ret


def parse_state(state):
    doc = fitz.Document(os.getcwd() + "/pdfs/2020-04-11_US_" + state +
                        "_Mobility_Report_en.pdf")
    data = []

    for i in range(2, doc.pageCount-1):
        for entry in parse_page(doc, i):
            entry["state"] = state
            entry["page"] = i
            data.append(entry)

    outname = os.getcwd() + "data/{}.json.gz".format(state)

    df = pd.DataFrame(data)
    if len(df.columns) > 0:
        ncounties = df['county'].nunique()
        print("Parsed {} plots for ".format(len(df)) +
              "{} counties in {}".format(ncounties, state))
        df = df[["state", "county", "category", "change", "changecalc",
                 "dates", "values", "page"]]
    return df


states = [x.split("_US_", 1)[1].split("_Mobility", 1)[0] for x
          in glob.glob("pdfs/*.pdf")]
dfs = []
for state in states:
    dfs.append(parse_state(state))
#dfs.append(parse_state('Vermont'))
df = pd.concat(dfs).reset_index(drop=True)
data = []
for i, row in tqdm(df.iterrows()):
    # do a little clean up and unstack the dates/values as separate rows
    dorig = dict()
    dorig["state"] = row["state"].replace("_", " ")
    dorig["county"] = row["county"]
    dorig["category"] = row["category"].replace(" & ",
                                                "/").replace(" ", "").lower()
    dorig["page"] = row["page"]
    dorig["change"] = row["change"]
    dorig["changecalc"] = row["changecalc"]
    for x, y in zip(row["dates"], row["values"]):
        d = dorig.copy()
        d["date"] = x
        d["value"] = y
        data.append(d)
df = pd.DataFrame(data)
df.to_json("data/data.json.gz", orient="records", indent=2)

dfc = pd.read_json("data/data.json.gz")
#dfc["date"] = pd.to_datetime(dfc["date"])
