Amazon Order Scraper
====================

This is a simple script using the Python selenium library to scrape all your Amazon
orders and create handy PDFs for receipt/tax purposes.

To use::

    git clone https://github.com/jagatsingh/amzscraper.git
    cd amzscraper
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install .
    amzscraper --user 'email' --password 'password' 2024

If it does need to download a page from Amazon, a random sleep is inserted to throttle
connections to the server.

Orders will be downloaded to the ``orders/`` directory in your current directory by
default

For further options, see::

    amzscraper -h

Requirements
------------

* Python 3.12+
* ``wkhtmltopdf`` installed and in your ``PATH``

Credits
-------

This is loosely based on an `earlier project <http://chase-seibert.github.io/blog/2011/01/15/backup-your-amazon-order-history-with-python.html>`_
by Chase Seibert.

This version changes https://github.com/tobiasmcnulty/amzscraper to update the dependecies to latest version. It also
removes email related code to simplify.
