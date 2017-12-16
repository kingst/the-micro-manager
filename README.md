# the-micro-manager

to install

`pip install -r requirements.txt`

or you might need sudo

`sudo pip install -r requirements.txt`

then you need to install API credentials in the `creds.py` file, which
should look something like this:

```
CLIENT_ID = 'NOT_A_REAL_ID'
CLIENT_SECRET = 'NOT_A_REAL_SECRET'
```

the run the main python script

`./main.py`

and visit the landing page for the app:

`http://localhost:8080`

link your github account, then you should be good to go. If your org
commits aren't showing up, try using a personal token instead:

`http://localhost:8080/cheat_code`

Note: the data doesn't update automatically, you need to go refresh it
manually (select the link from the nav bar)
