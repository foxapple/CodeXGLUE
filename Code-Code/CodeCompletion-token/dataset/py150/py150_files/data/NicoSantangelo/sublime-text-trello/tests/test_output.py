import unittest

from .util import TrelloCardMock, TrelloNotificationMock
from output import Output

class OutputTests(unittest.TestCase):
    def test_comments_returns_a_message_when_there_are_no_comments(self):
        self.assertEqual(Output.comments([]), "The card has no comments")

    def test_comments_returns_an_ordered_list(self):
        user = "Tim"
        other_user = "Minchin"
        comments = [{ 'username': user, 'text': "first" }, { 'username': other_user, 'text': "first!!" }, { 'username': user, 'text': "c'mon guys" }]
        result = "1) Tim: first\n2) Minchin: first!!\n3) Tim: c'mon guys\n"
        self.assertEqual(Output.comments(comments), result)

    def test_card_returns_the_information_of_the_card(self):
        card = TrelloCardMock()
        output = """card_name (card_url)
    card_desc

The card has:
    2 members
    2 comments
    4 votes
    3 attachments
    3 labels ( Green: Ok, Yellow, Red: Urgent )"""
        self.assertEqual(Output.card(card), output)

    def test_notifications_shows_the_available_information_and_the_amount(self):
        notification1 = TrelloNotificationMock("addedToBoard", { 'board': { 'name': 'Some board Name' } })
        notification2 = TrelloNotificationMock("commentCard", { 'card': { 'name': 'Some card name' } })
        notifications = [notification1, notification2]

        output = """Total unread: 2

1) Nofitication type: addedToBoard
Board: Some board Name

2) Nofitication type: commentCard
Card: Some card name"""

        self.assertEqual(Output.notifications(notifications), output)


if __name__ == '__main__':
    unittest.main()