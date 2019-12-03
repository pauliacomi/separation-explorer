from threading import Thread

import src.datastore


def on_server_loaded(server_context):
    ''' If present, this function is called when the server first starts. '''
    t = Thread(target=src.datastore.load, args=())
    t.setDaemon(True)
    t.start()


def on_server_unloaded(server_context):
    ''' If present, this function is called when the server shuts down. '''
    pass


def on_session_created(session_context):
    ''' If present, this function is called when a session is created. '''
    pass


def on_session_destroyed(session_context):
    ''' If present, this function is called when a session is closed. '''
    pass
