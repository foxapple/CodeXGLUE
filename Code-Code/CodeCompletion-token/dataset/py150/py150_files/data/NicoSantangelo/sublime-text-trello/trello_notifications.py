import requests

try:
    from trello import TrelloCommand
    from output import Output
except ImportError:
    from .trello import TrelloCommand
    from .output import Output

class TrelloNotificationsCommand(TrelloCommand):
    def work(self, connection):
        self.options = [
            { 'name': "Unread", 'action': self.show_unread },
            { 'name': "Read all", 'action': self.defer_read_all },
            { 'name': "Exit", 'action': self.noop }
        ]
        self.connection = connection
        self.show_quick_panel(self.items(), self.callback)

    def items(self):
        return [option['name'] for option in self.options]

    def callback(self, index):
        option = self.options[index]
        if not option is None:
            option['action']()

    def show_unread(self):
        self.view.run_command("trello_unread_notifications")

    def defer_read_all(self):
        self.defer(self.read_all)

    def read_all(self):
        try:
            self.connection.me.read_all_notifications()
        except requests.exceptions.HTTPError:
            first = "There was an error trying to read the notifications. This probably means that you need to grant the app 'account' privileges."
            second = "If you want to do this, revoke your current app (https://trello.com/username/account) and remove the token from your settings."
            third = "Then add 'account' to the scopes when re-accesing the app like this:\n%s,account.\n\nThanks!" % (self.token_url())
            self.show_output_panel_composing(first, second, third)

    def noop(self):
        pass

class TrelloUnreadNotificationsCommand(TrelloCommand):
    def work(self, connection):
        member = connection.me
        try:
            output = Output.notifications(member.unread_notifications())
            self.show_output_panel(output)
        except requests.exceptions.HTTPError as e:
            self.show_token_expired_help(e)
            raise e