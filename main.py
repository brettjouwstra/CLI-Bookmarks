#!/usr/local/bin/python3

import typer
from tinydb import TinyDB, Query
import os
from os.path import expanduser
import favicon
from bs4 import BeautifulSoup as bs
import requests
from typer import Option
from typing import Optional
import webbrowser
from fuzzywuzzy import fuzz, process
import jinja2

app = typer.Typer()

home = expanduser("~")
database_file = os.path.join(home, '.database_cli.json')

db = TinyDB(database_file)
query = Query()
find_list = Query()

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" />
    <style>
        body {
            font-family: sans-serif;
        }
        code, pre {
            font-family: monospace;
        }
        h1 code,
        h2 code,
        h3 code,
        h4 code,
        h5 code,
        h6 code {
            font-size: inherit;
        }
    </style>
</head>
<body>
<div class="container">
            <table class="table table-striped">
                <thead>
                    <tr>
                    <th scope="col">#</th>
                    <th scope="col">Title</th>
                    <th scope="col">URL</th>
                    <th scope="col">FavIcon</th>
                    <th scope="col">Tags</th>
                    </tr>
                </thead>
            <tbody>
            {%for x in content %}
                <tr>
                    <td>{{ x['Count'] }}</td>
                    <td>{{ x['Title'] }}</td> 
                    <td><a href="{{ x['URL'] }}">Visit Site</td> 
                    <td><img style='width: 40px;' src=' {{ x['Icon'] }}'/></td> 
                    <td>{% for y in x['Tags'] %}
                        <a href="#" class="badge badge-secondary">{{ y }}</a>
                        {% endfor %}</td>
                    </td>
                </tr>
            {% endfor %}
            </tbody>
        </div>
    </body>
</html>"""

@app.command(help="Returns the number of entries")
def count(count: str = None):
    typer.echo(len(db.all()))


@app.command(help="Create an entry given a URL")
def add(url: str):
    tags = typer.prompt("Any tags? - comma seperated list")
    tags = tags.lower()
    
    try:
        icon = favicon.get(url)[0][0]
    except:
        icon = None
    html = requests.get(url)

    soup = bs(html.content, 'html.parser')
    title = soup.find('title')
    title = title.get_text()

    db.insert({ "Title": title, "URL": url, "Icon": icon, "Tags": tags.split(",") })
    
    typer.echo("{} saved with - Title: {} - Favicon: {}".format(typer.style(url, fg=typer.colors.GREEN, bold=False), typer.style(title, fg=typer.colors.GREEN, bold=True), typer.style(icon, fg=typer.colors.GREEN, bold=True) ))



@app.command(help="Search for an entry by title given a search term. Provide the second, optional, argument 'True' to open the returned URL in the default browser")
def find(title: str, open: Optional[bool] = typer.Argument(False)):
    lookup = db.search(query.Title == title)
    for item in lookup:
        results = "Title: {}, URL: {}, Tags: {}".format( typer.style(item['Title'], fg=typer.colors.BRIGHT_BLUE, bold=True), 
                    typer.style(item['URL'], fg=typer.colors.RED, bold=False), typer.style( str(item['Tags']) , fg=typer.colors.YELLOW, bold=False) )
    if open != False:
        webbrowser.open_new(lookup[0]['URL'])
    typer.echo(results)


@app.command("tags", help="Provide a single word search term and all entries with tags that match the given term will be returned.")
def search_tags(tag: str):
    lookup = db.search(query.Tags.any(tag))
    typer.echo(lookup)


@app.command("list", help="Lists all entries") # This over rides the usual call - which would be "collection"
def collection():
    lookup = db.all()
    typer.echo(lookup)


@app.command("text", help="Given a string, fuzzy search the entries and return the top three results.")
def fuzzysearch(term: str):
    choices = db.all()
    guess = process.extract(term, choices, limit=3)
    final = []
    for item in guess:
        results = "Entry: {} \n Percent Certain: {}".format(item[0], item[1])
        final.append(results)
    typer.echo(final)


@app.command("dashboard", help="Open a webpage with the entries presented")
def dashboard_page():
    entries = db.all()
    count = 1
    list_of_rows = []
    for item in entries:
        if item['Icon'] == None:
            item['Icon'] = "https://storage.googleapis.com/template-design/icons/svg_icons_big-list/windows/page-question.svg"
        list_of_rows.append({ "Count": count, "Title": item['Title'], "URL": item['URL'], "Icon": item['Icon'], "Tags": item['Tags'] })
        count += 1
    
    doc = jinja2.Template(TEMPLATE).render(content=list_of_rows)
    open(os.path.join(home, 'Dashboard.html'), 'w').write(doc)
    #output.write(doc, 'w')
    #webbrowser.open_new("file:///{}".format(os.path.join(home, 'Dashboard.html')))
    typer.echo("Done")
    

if __name__ == "__main__":
    app()
