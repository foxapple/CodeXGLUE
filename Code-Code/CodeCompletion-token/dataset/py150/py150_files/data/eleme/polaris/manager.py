

def runserver(port=9500):
    from polaris import create_app
    from polaris.models import db
    app = create_app()
    app.debug = True
    db.app = app
    db.create_all()
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    runserver()
