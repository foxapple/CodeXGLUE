from unittest import TestCase

from tests.factories import SentencedIEDocFactory
from iepy.data.models import IEDocument
from iepy.preprocess.pipeline import PreProcessSteps
from iepy.preprocess.tagger import TaggerRunner, StanfordTaggerRunner
from .manager_case import ManagerTestCase


class TestTaggerRunner(ManagerTestCase):
    ManagerClass = IEDocument

    def test_tagger_runner_is_calling_postagger(self):
        doc = SentencedIEDocFactory(text='Some sentence. And some other. Indeed!')
        expected_postags = [['DT', 'NN', '.'], ['CC', 'DT', 'JJ', '.'], ['RB', '.']]
        i = iter(expected_postags)

        def postagger(sents):
            return (zip(sent, next(i)) for sent in sents)
        tag = TaggerRunner(postagger)
        tag(doc)
        self.assertTrue(doc.was_preprocess_step_done(PreProcessSteps.tagging))
        self.assertEqual(doc.postags, sum(expected_postags, []))

    def test_tagger_runner_not_overriding_by_default(self):
        doc = SentencedIEDocFactory(text='Some sentence. And some other. Indeed!')
        postagger1 = lambda sents: [[(x, 'A') for x in sent] for sent in sents]
        postagger2 = lambda sents: [[(x, 'B') for x in sent] for sent in sents]
        tag = TaggerRunner(postagger1)
        tag(doc)
        tag.postagger = postagger2  # XXX: accessing implementation
        tag(doc)
        self.assertTrue(all(x == 'A' for x in doc.postags))

    def test_tagger_runner_overriding_when_selected(self):
        doc = SentencedIEDocFactory(text='Some sentence. And some other. Indeed!')
        postagger1 = lambda sents: [[(x, 'A') for x in sent] for sent in sents]
        postagger2 = lambda sents: [[(x, 'B') for x in sent] for sent in sents]
        tag = TaggerRunner(postagger1, override=True)
        tag(doc)
        tag.postagger = postagger2  # XXX: accessing implementation
        tag(doc)
        self.assertTrue(all(x == 'B' for x in doc.postags))

