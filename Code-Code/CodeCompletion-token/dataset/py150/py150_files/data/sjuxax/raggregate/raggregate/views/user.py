import sqlalchemy

from raggregate.models import DBSession
from raggregate.models.user import User
from raggregate.models.ban import Ban
from raggregate.queries import users
from raggregate.queries import submission
from raggregate.queries import general

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound

from raggregate.login_adapters import fb
from raggregate.login_adapters import LoginAdapterExc

from datetime import timedelta

@view_config(renderer='login.mak', route_name='login')
def login(request):
    #@FIXME: this uses a request handling method with success with which I was experimenting
    # it is not used elsewhere and is a pain to read and write
    # success = False causes a page to stop drawing and "error out"
    # some error conditions therefore don't set success to false because it's more convenient
    # to draw the rest of the page.
    #
    # someone should adapt this to be less success-centric and read less branchy.
    s = request.session

    success = True

    # check for facebook login, provided by Facebook's JS SDK
    try:
        fb_cookie = fb.extract_from_cookie(request)
        try:
            u = users.get_user_by_name(fb_cookie['local_username'])
        except sqlalchemy.orm.exc.NoResultFound:
            u = fb.create_local_user(fb_cookie['info'], fb_cookie['local_username'], request = request)
        try:
            users.login_user(request, u, None, bypass_password = True)
        except LoginAdapterExc:
            pass
    except LoginAdapterExc:
        pass

    if 'logout' in request.session['safe_params']:
        if 'logged_in' in s:
            del s['logged_in']
            del s['users.id']
            if 'u_fbgraph' in s:
                del s['u_fbgraph']
                del s['u_fbinfo']
            if 'u_twit' in s:
                del s['u_twit']
            s['message'] = "You have been logged out, thanks."
            success = True
        else:
            s['message'] = "You are not logged in."
            success = True
    else:
        logged_in = False
        if 'logged_in' in s:
            s['message'] = "You are already logged in."
            logged_in = True
        else:
            if 'message' not in s:
                if 'last_login_status' in s:
                    s['message'] = s['last_login_status']
                    del s['last_login_status']
                else:
                    s['message'] = "Please log in."
        p = request.session['safe_post']
        prm = request.session['safe_params']
        username = None
        if 'username' in prm:
            username = general.strip_all_html(prm['username'])
        if p:
            dbsession = DBSession()
            if request.session['safe_get']['act'] == 'register':
                if logged_in:
                    try:
                        u = users.get_user_by_id(s['users.id'])
                        if u.temporary:
                            users.create_user(temp_to_perm = True, extant_id = s['users.id'], username = username, password = p['password'], email = p['email'], origination = 'site')
                            s['message'] = "Your anonymous profile has been converted, thanks."
                        else:
                            s['message'] = "You can't register while you're logged in."
                    except sqlalchemy.exc.IntegrityError:
                        s['message'] = "This username is already registered, sorry."
                        dbsession.rollback()
                else:
                    try:
                        users.create_user(username = username, password = p['password'], email = p['email'], origination = 'site')
                        s['message'] = "Successfully registered."
                        success = True
                    except sqlalchemy.exc.IntegrityError:
                        s['message'] = "This username is already registered, sorry."
                        success = False
                        dbsession.rollback()
            elif request.session['safe_get']['act'] == 'update_pw':
                if p['new_password'] != p['new_password_confirm']:
                    s['message'] = 'New password doesn\'t match confirmation, please try again.'
                else:
                    u = None

                    if s['logged_in_admin']:
                        if 'user_id' in prm:
                            u = users.get_user_by_id(prm['user_id'])

                    if u == None:
                        u = users.get_user_by_id(s['users.id'])

                    if u.verify_pw(p['old_password']) or s['logged_in_admin']:
                        u.password = u.hash_pw(p['new_password'])
                        dbsession.add(u)
                        s['message'] = 'Password updated.'
                        success = True
                    else:
                        s['message'] = 'Old password invalid.'
            elif request.session['safe_get']['act'] == 'forgot_pass':
                user = users.get_user_by_email(p['email'])
                if not user:
                    s['message'] = "That email isn't registered"
                else:
                    s['message'] = "Check your mail for a confirmation message."
                    users.send_lost_password_verify_email(request, user)
            else:
                try:
                    u = users.get_user_by_name(username)
                    try:
                        users.login_user(request, u, p['password'])
                        s['message'] = "Good, logged in"
                        success = True
                        return HTTPFound(request.route_url('post'))
                    except LoginAdapterExc:
                        s['message'] = "Incorrect password."
                        success = False
                except sqlalchemy.orm.exc.NoResultFound:
                    s['message'] = "Sorry, I don't know you."
                    success = False

    return {'success': success,}

@view_config(renderer='login.mak', route_name='twit_sign')
def twit_sign(request):
    from raggregate.login_adapters import twitter
    if 'oauth_verifier' not in request.session['safe_params']:
        auth_toks = twitter.start_auth(request)
        request.session['tmp_tok_store'] = auth_toks
        return HTTPFound(auth_toks['auth_url'])
    else:
        twit_auth = twitter.complete_auth(request, request.session['tmp_tok_store'])
        del request.session['tmp_tok_store']
        try:
            users.login_user(request, twit_auth['u'], None, bypass_password = True)
        except:
            request.session['last_login_status'] = 'Sorry, your password was wrong.'
            #raise
        return HTTPFound('/post')

@view_config(renderer='save.mak', route_name='save')
def save(request):
    s = request.session
    p = request.session['safe_params']
    u = None
    op = 'add'
    vote_dict = {}

    if 'story_id' in p and 'logged_in' in s:
        dbsession = DBSession()
        u = users.get_user_by_id(s['users.id'])
        to_save = submission.get_story_by_id(p['story_id'])
        if 'op' in p:
            op = p['op']
        if op == 'add':
            if to_save not in u.saved:
                u.saved.append(to_save)
                dbsession.add(u)
            s['message'] = 'Successfully saved {0}'.format(to_save.title)
        elif op == 'del':
            if to_save in u.saved:
                u.saved.remove(to_save)
                dbsession.add(u)
            s['message'] = 'Successfully unsaved {0}'.format(to_save.title)
    elif 'logged_in' in s:
        u = users.get_user_by_id(s['users.id'])

    if u:
        vds = []
        for i in u.saved:
            vds.append(users.get_user_votes(s['users.id'], "on_submission", i.id))
        for vd in vds:
            if type(vd) == dict:
                vote_dict.update(vd)

    return {'saved': u.saved, 'vote_dict': vote_dict, }

@view_config(renderer='follow.mak', route_name='follow')
def follow(request):
    s = request.session
    p = request.session['safe_params']
    message = ''

    if 'logged_in' not in s:
        s['message'] = 'Sorry, you must be logged in to use the follow feature.'
        return {'success': False, 'code': 'ENOLOGIN'}

    if 'follow_id' in p and 'logged_in' in s:
        dbsession = DBSession()
        #@TODO: replace with model-wide method to get logged-in user object
        u = users.get_user_by_id(s['users.id'])
        to_follow = users.get_user_by_id(p['follow_id'])
        op = 'add'
        if 'op' in p:
            op = p['op']
        if to_follow not in u.follows and op == 'add':
            u.follows.append(to_follow)
            del(s['followed_users'])
            dbsession.add(u)
            message = 'Successfully following {0}'.format(to_follow.display_name())
        elif to_follow in u.follows and op == 'del':
            u.follows.remove(to_follow)
            del(s['followed_users'])
            dbsession.add(u)
            message = 'Successfully unfollowed {0}'.format(to_follow.display_name())
    elif 'logged_in' in s:
        u = users.get_user_by_id(s['users.id'])

    vds = []
    vote_dict = {}

    if u:
       for i in u.follows:
           for story in i.submissions:
               #@FIXME: this is probably quite slow
               vds.append(users.get_user_votes(u.id, "on_submission", story.id))
       for vd in vds:
           if type(vd) == dict:
               vote_dict.update(vd)

    s['message'] = message
    return {'follows': u.follows, 'vote_dict': vote_dict}

@view_config(renderer='notify.mak', route_name='notify')
def notify(request):
    from raggregate.queries import notify as notify_queries
    s = request.session
    p = request.session['safe_params']
    u = None
    op = 'add'
    vote_dict = {}

    notifyd = notify_queries.get_notify_by_user_id(s['users.id'])
    notifyd_ids = [str(i.target_id) for i in notify_queries.get_notify_by_user_id(s['users.id'])]
    if 'target_id' in p and 'logged_in' in s:
        dbsession = DBSession()

        uid = s['users.id']
        to_notify = p['target_id']
        if 'op' in p:
            op = p['op']
        if op == 'add':
            if to_notify not in notifyd_ids:
                notify_queries.create_notify(uid, to_notify, s['users.id'])
            s['message'] = 'Successfully notified'
        elif op == 'del':
            if to_notify in notifyd_ids:
                notify_queries.delete_notify(user_id = uid, target_id  = to_notify)
            s['message'] = 'Successfully de-notified'
    elif 'logged_in' in s:
        u = users.get_user_by_id(s['users.id'])


    # the template expects a set of stories to render
    notifyd_stories = [submission.get_story_by_id(i.target_id) for i in notifyd if i.target_type == 'submission']
    notifyd_comments = [submission.get_comment_by_id(i.target_id) for i in notifyd if i.target_type == 'comment']

    if u:
        vds = []
        for i in notifyd_stories:
            vds.append(users.get_user_votes(s['users.id'], "on_submission", i.id))
        for vd in vds:
            if type(vd) == dict:
                vote_dict.update(vd)

    return {'notifyd_stories': notifyd_stories,
            'notifyd_comments': notifyd_comments,
            'vote_dict': vote_dict, }

@view_config(renderer="user_info.mak", route_name='user_info')
def user_info(request):
    import hashlib
    import os
    from raggregate.queries import user_preference as up

    r = request
    ses = request.session
    p = ses['safe_post']

    edit_mode = False
    user_id = None

    if 'user_id' in r.params:
        user_id = r.params['user_id']

    if 'logged_in' in ses and 'user_id' not in r.params:
        user_id = ses['users.id']

    if 'logged_in' in ses and (user_id == str(ses['users.id']) or users.get_user_by_id(ses['users.id']).is_user_admin()):
        edit_mode = True

    u = users.get_user_by_id(user_id)
    params = up.get_user_prefs(user_id)

    if p and edit_mode:
        dbsession = DBSession()
        u.about_me = p['about_me']
        if p['email'] == "":
            u.email = None
        else:
            u.email = p['email']
        if r.POST['picture'] != '':
            orig_filename = r.POST['picture'].filename
            up_dir = r.registry.settings['user.picture_upload_directory']

            u.picture = users.add_user_picture(orig_filename, str(u.id)[:7], up_dir, r.POST['picture'].file)

        dbsession.add(u)

    response = {'edit_mode': edit_mode, 'u': u}
    response.update(params)
    return response

@view_config(renderer='user_info.mak', route_name='user_preferences')
def user_preferences(request):
    from raggregate.queries import user_preference as up
    from webob.multidict import MultiDict

    user_id = request.session.get('users.id', None)
    prefs = {}

    if request.POST:
        prefs['link_to_story'] = request.POST.get('prop-link-directly-to-story', 'off')
        prefs['reg_for_notifications'] = request.POST.get('prop-auto-reg-for-notifications', 'off')
        up.set_user_prefs(user_id, prefs)
    else:
        prefs = up.get_user_prefs(user_id)

    return prefs


@view_config(renderer="ban.mak", route_name="ban")
def ban(request):
    r = request
    s = request.session
    p = s['safe_post']

    if 'logged_in_admin' not in s or s['logged_in_admin'] == False:
        return HTTPNotFound()

    if 'ip' in p:
        if p['ip'].strip() == '':
            ip = None
        else:
            ip = p['ip']

        if p['username'].strip() == '':
            username = None
            user_id = None
        else:
            username = p['username']

        if p['duration'].strip() == 'infinite':
            duration = None
        else:
            duration = "timedelta({0})".format(p['duration'])
            duration = eval(duration)

        if username:
            user_id = users.get_user_by_name(username).id

        b = Ban(ip = ip, username = username, duration = duration, user_id = user_id, added_by = s['users.id'])
        dbsession = DBSession()
        dbsession.add(b)

    bans = general.list_bans()
    return {'bans': bans}
