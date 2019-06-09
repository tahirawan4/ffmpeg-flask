# ffmpeg-flask


Command to setup project.

### Setting up Environment

    pipenv shell  # it will create a virtual env
    pipenv install # it will install all the requirements
    export FLASK_APP = project
    flask run
    
### Running migrations

    flask db init #init the database
    flask db migrate  #it will create migrations, if there is any changes in models 
    flask db upgrade  #it will reflect models update in databse files 

For file type detection => please install https://github.com/ahupp/python-magic