*This is the open source fork of what powers breezeminder.com*

breezeminder
============

Reminders for your Breeze Card.


Dependencies
------------
* Flask
* Celery
* MongoDB
* Python 2.6 or 2.7
* Redis
* Memcached


Getting Started
---------------
You'll first need to setup a virtual env for working::

    virtualenv -p python2.6 --system-site-packages /path/to/venv
    mkdir /path/to/venv/var
    git clone http://github.com/shaunduncan/breezeminder.git /path/to/venv/src/breezeminder

At this point, activate the venv and install requirements::

    cd /path/to/venv
    source bin/activate
    pip install -r /path/to/venv/src/breezeminder/requirements.txt

Start up mongo::

    mongod --port 27017 --fork --logpath=/opt/venv/breezeminder/var/mongodb.log --dbpath=/opt/venv/breezeminder/var/

You will also want to import base datasets for the app to use::

    mongorestore --db breezeminder --collection wireless lib/carriers.bson
    mongorestore --db breezeminder --collection reminder_types lib/reminder_types.bson

Start up celery/redis::

    redis-server
    python2.6 manage.py celeryd -B

Get started with developing the app and run the local webserver::

    cd /path/to/venv/src/breezeminder
    python setup.py develop
    python breezeminder/runserver.py


Proof of Concept
----------------
The Breeze Card system has an endpoint to pull down current status::

    import requests

    payload = {
        # Fake Card Number
        'cardnumber': '0000111122223333',
        'submitButton.x': '0',
        'submitButton.y': '0'
    }

    resp = requests.post('https://balance.breezecard.com/breezeWeb/cardnumber_qa.do',
                         data=payload)
    print resp.content


Contributing
============
This is the open source fork that runs BreezeMinder.com. Please feel free to submit
issues, pull requests, etc.
