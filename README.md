[![DOI](https://joss.theoj.org/papers/10.21105/joss.02410/status.svg)](https://doi.org/10.21105/joss.02410)

VIIME
========

Getting started (Running natively)
----------------------------------

This project includes a `Pipfile` to help set up a virtual environment for
VIIME. To set up the virtual environment

```sh
pipenv install
```

and to enter it

```sh
pipenv shell
```

VIIME is configured from a `.env` file present in the current directory where
it is executed.  See the included [.env_example](./.env_example) for an example
(or try [.env_pwd](./env_pwd), which saves DB and uploaded files in the checked
out directory rather than your home directory).  Once the environment is in
place, you will need to initialize the tables by running

```sh
mkdir viime_sqlite
viime-cli create-tables
```

This will create a data directory according to the `SQLALCHEMY_DATABASE_URI` and
`UPLOAD_FOLDER` environment variables defined in the `.env` file.

Start the development server by running:

```sh
flask run
```

To start the frontend, run:

```sh
cd web/
yarn
yarn serve
```

R Processing Functions using OpenCPU
------------------------------------

The [devops](./devops) directory contains everything needed to spin up an
[OpenCPU](https://www.opencpu.org/) instance with all dependencies necessary
for the processing backend.  To run it locally, build the docker container

```sh
cd devops
docker build -t viime .
```

and start the instance

```sh
docker run -it --rm -p 8004:8004 viime
```

You may find that changes to the position or size of the window in which the
Docker image runs will cause the service to terminate with `SIGWINCH`; this is
actually intended behavior and can be avoided by running the image *without*
allocating a pseudo-terminal and keeping `stdin` open:

```sh
docker run --rm --name viime -p 8004:8004 viime
```

To stop this container, use a command like `docker stop viime` from another
terminal.

This installation includes a custom R package called
[viime](devops/viime), which contains all functions that are exposed to
the API server for CSV file processing.  Functions contained in this package
should accept a path to a CSV file as an argument and return a data frame.  The
(work-in-progress) backend code at [viime/opencpu.py](viime/opencpu.py)
handles the communication between pandas and R data frames.  To add additional
methods exposed to the API server, add the function to the viime package and
rebuild the docker image.

Database migration
------------------

This application uses `flask-migrate` to manage database migrations. To create a migration after changing models, run:

```sh
flask db migrate
```

To migrate to the latest database schema, run:

```sh
flask db upgrade
```

Getting started (`docker-compose`)
----------------------------------
You can run the backend components for this project with Docker Compose:

```sh
cd devops/docker
docker-compose up
```

This command will spin up two Docker containers named `docker_backend_1` and
`docker_opencpu_1`.

Note, the web client will still need to be started using `yarn serve`.

Once the client is running, you can use it to upload the CSV files found
in the [sample data](samples/data) directory of this repository.
