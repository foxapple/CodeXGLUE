import os
import re
import logging
import sqlite3

NOTE_REGEX = re.compile(r'^!([^\s]+.*)')


class NotesPlugin(object):
    logger = None

    def __init__(self, cardinal, config):
        # Initialize logging
        self.logger = logging.getLogger(__name__)

        if config is not None:
            if config['shout_nick_notes_on_join']:
                self.callback_id = cardinal.event_manager.register_callback(
                    'irc.join', self.join_callback
                )

        # Connect to or create the note database
        self._connect_or_create_db(cardinal)

    def join_callback(self, cardinal, user, channel):
        content = self._get_note_from_db(user.group(1))
        if content:
            cardinal.sendMsg(channel, "[%s] %s" % (user.group(1), content))

    def _connect_or_create_db(self, cardinal):
        try:
            self.conn = sqlite3.connect(os.path.join(
                cardinal.storage_path,
                'database',
                'notes-%s.db' % cardinal.network
            ))
        except Exception:
            self.conn = None
            self.logger.exception("Unable to access local notes database")
            return

        c = self.conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS notes ("
                  "title text collate nocase PRIMARY KEY, "
                  "content text collate nocase)")
        self.conn.commit()

    def add_note(self, cardinal, user, channel, msg):
        if not self.conn:
            cardinal.sendMsg("Unable to access notes database.")
            return

        message = msg.split('=', 1)
        title_message = message[0].split(' ', 1)
        if len(message) < 2 or len(title_message) < 2:
            cardinal.sendMsg(channel, "Syntax: .addnote <title>=<content>")
            return

        title = title_message[1].strip()
        content = message[1].strip()
        if len(title) == 0 or len(content) == 0:
            cardinal.sendMsg(channel, "Syntax: .addnote <title>=<content>")
            return

        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO notes (title, content) VALUES(?, ?)",
                  (title, content))
        self.conn.commit()

        cardinal.sendMsg(channel, "Saved note '%s'." % title)

    add_note.commands = ['addnote']
    add_note.help = ["Saves a note to the database for retrieval later.",
                     "Syntax: .addnote <title>=<content>"]

    def delete_note(self, cardinal, user, channel, msg):
        if not self.conn:
            cardinal.sendMsg(channel, "Unable to access notes database.")
            return

        msg = msg.split(' ', 1)
        if len(msg) < 2 or len(msg[1]) == 0:
            cardinal.sendMsg(channel, "Syntax: .delnote <title>")
            return

        title = msg[1]
        c = self.conn.cursor()
        c.execute("SELECT COUNT(title) FROM notes WHERE title=?", (title,))
        result = c.fetchone()

        if not result[0]:
            cardinal.sendMsg(channel, "No note found under '%s'." % title)
            return

        c.execute("DELETE FROM notes WHERE title = ?", (title,))
        self.conn.commit()

        cardinal.sendMsg(channel, "Deleted note saved under '%s'." % title)

    delete_note.commands = ['delnote']
    delete_note.help = ["Deletes a note from the database.",
                        "Syntax: .delnote <title>"]

    def get_note(self, cardinal, user, channel, msg):
        if not self.conn:
            cardinal.sendMsg(channel, "Unable to access notes database.")
            return

        message = msg.split(' ', 1)
        # Check if they are using ! syntax.
        if message[0][0] == '!':
            title = ' '.join(message)[1:]
        else:
            if len(message) != 2:
                cardinal.sendMsg(channel, "Syntax: .note <title>")
                return

            # Grab title for .note syntax.
            title = message[1]

        content = self._get_note_from_db(title)
        if not content:
            cardinal.sendMsg(channel, "No note found under '%s'." % title)
            return

        cardinal.sendMsg(channel, "%s: %s" % (title, content))

    get_note.commands = ["note"]
    get_note.regex = NOTE_REGEX
    get_note.help = ["Retrieve a saved note.",
                     "Syntax: .note <title>"]

    def _get_note_from_db(self, title):
        c = self.conn.cursor()
        c.execute("SELECT content FROM notes WHERE title=?", (title,))
        result = c.fetchone()
        if not result:
            return False
        else:
            return bytes(result[0])

    def close(self, cardinal):
        if hasattr(self, 'callback_id'):
            cardinal.event_manager.remove_callback('irc.join',
                                                   self.callback_id)


def setup(cardinal, config):
    return NotesPlugin(cardinal, config)
