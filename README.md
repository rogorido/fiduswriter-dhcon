# FidusWriter-DHDConf

FidusWriter-DHDConf is a [Fidus Writer](https://github.com/fiduswriter/fiduswriter/) plugin used to organize collaborative writing for submissions to [DHD conferences](https://dig-hum.de).

Users can login with their [conftool](https://www.conftool.net/en/index.html) credentials.

## Setup

In your `configuration.py` add `dhdconf` to the list of installed apps:

```py
INSTALLED_APPS = [
	...
    "dhdconf"
]
```

In the same file add the authentication backend `ConftoolBackend` to allow login via conftool. In the same setting keep Djangos `ModelBackend` if you want to allow logins by users who are not registered in conftool (e.g. for admin accounts).

```py
AUTHENTICATION_BACKENDS = [
    "dhdconf.conftool.auth.ConftoolBackend",
    "django.contrib.auth.backends.ModelBackend",
]
```

We assume that users will login with their conftool credentials and email verification is handled by conftool. So we can adjust some authentication settings

```py
PASSWORD_LOGIN = True
REGISTRATION_OPEN = False
SOCIALACCOUNT_OPEN = False
ACCOUNT_EMAIL_VERIFICATION = "none"
```

Add our middleware which restrict access to some fidus functionality:

```py
MIDDLEWARE = [
    "dhdconf.middleware.RequestBlockingMiddleware"
]
```

Have a look at [app_settings.py](fiduswriter/dhdconf/app_settings.py) for our settings. You can override these in your `configuration.py`.

Run our setup task to finish the installation:

```sh
fiduswriter dhdconf_setup
```

## Local setup for development

For development pruposes you can clone the fiduswriter repoy and symlink this repo into it.

```sh
git clone git@github.com:fiduswriter/fiduswriter.git fiduswriter
cd fiduswriter

# Create a virtual environment and export env variables
python -m venv ./venv
cat <<-EOF >> venv/bin/activate
export CONFTOOL_URL=https://www.conftool.net/demo/dhdtest_26j/rest.php
export CONFTOOL_APIPASS=<apipass>
EOF
source venv/bin/activate

cd fiduswriter
pip install -r requirements.txt -r dev-requirements.txt -r test-requirements.txt -r postgresql-requirements.txt ipython

ln -s ../../fiduswriter-dhdconf-plugin/fiduswriter/dhdconf dhdconf

./manage.py migrate
./manage.py dhdconf_setup
./manage.py runserver
```

Run our tests with

```sh
./manage.py jest
./manage.py test dhdconf
```

If on sqlite locally, you need to add a `TEST` configuration in `configuration.py`:

```py
DATABASES = {
    "default": {
        ...
        "TEST": {
            "NAME": "/tmp/fidustest.sql"
        }
    }
}
```
