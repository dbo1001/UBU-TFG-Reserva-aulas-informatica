from __init__ import app,db
import flask
from models import O365OAuthToken
from oauth_helpers import (
    datetime_from_timestamp,
    get_oauth_token,
    get_jwt_from_id_token,
    sign_in_url,
    get_events,
    refresh_oauth_token
    )
import json

@app.route('/')
def hello_world():
    return flask.render_template('home.html', o365_sign_in_url=sign_in_url())


@app.route('/connect/get_token/')
def connect_o365_token():
    code = flask.request.args.get('code')
    print('code: '+code)
    if not code:
        app.logger.error("NO 'code' VALUE RECEIVED")
        return flask.Response(status=400)

    token = get_oauth_token(code)

    jwt = get_jwt_from_id_token(token['id_token']) #JSON Web Token

    oauth_token = O365OAuthToken.query.filter(O365OAuthToken.user_email == jwt['email']).first()

    if not oauth_token:
        app.logger.info('CREATING new O365OAuthToken for {}'.format(jwt['email']))
        oauth_token = O365OAuthToken(
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            expires_on=datetime_from_timestamp(token['expires_in']),
            user_email=jwt['email'],
            token_type=token['token_type'],
            #resource=token['resource'],
            scope=token['scope']
        )
        #db.session.add(oauth_token)
    else:
        app.logger.info('UPDATING existing O365OAuthToken for {}'.format(jwt['email']))
        oauth_token.access_token = token['access_token']
        oauth_token.refresh_token = token['refresh_token']
        oauth_token.expires_on = datetime_from_timestamp(token['expires_on'])
        oauth_token.token_type = token['token_type']
        #oauth_token.resource = token['resource']
        oauth_token.scope = token['scope']
    
    #db.session.commit()

    flask.session['user_email'] = oauth_token.user_email
    flask.session['access_token'] = oauth_token.access_token
    flask.session['refresh_token'] = oauth_token.refresh_token
    return flask.redirect('/')

@app.route('/events')
def events():
    acc_token = flask.session['access_token']
    if not acc_token:
        return flask.redirect('/')
    else:
        events = get_events(acc_token)
        context = { 'events': events['value'] } #Obtener solo los eventos    
        eventosExistentes = context['events']
        json1_data = json.dumps(eventosExistentes) #Transformar los datos del JSON en un dict
        print(json1_data)

        return flask.render_template('events.html', dictEvents = eventosExistentes)

if __name__ == '__main__':
    db.init_app(app)
    db.create_all()
    app.run()