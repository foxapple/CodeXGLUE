# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import unittest

from flask_reveal.app import FlaskReveal
from flask_reveal.blueprints.reveal import load_markdown_slides


class BlueprintTestCase(unittest.TestCase):
    slides = ['Slide1', 'Slide2', 'Slide3']

    def create_presentation_structure(self, slides=None):
        root = tempfile.mkdtemp()
        media = tempfile.mkdtemp()

        fd_cfg, config = tempfile.mkstemp('.py', dir=root)
        fd_img, image = tempfile.mkstemp('.jpg', dir=media)

        os.close(fd_cfg)
        os.close(fd_img)

        for index, slide in enumerate(slides):
            fd, _ = tempfile.mkstemp('.md', str(index), root)
            with os.fdopen(fd, 'w') as file:
                file.write(slide)

        return dict(root=root,
                    media=media,
                    config=config,
                    image=os.path.basename(image))

    def create_client(self, presentation_root, media_root, config):
        app = FlaskReveal('flask_reveal')

        app.load_user_config(presentation_root, media_root, config)
        app.config['TESTING'] = True

        return app.test_client()

    def setUp(self):
        self.presentation = self.create_presentation_structure(self.slides)

    def tearDown(self):
        shutil.rmtree(self.presentation['root'])

    def test_presentation_view_status(self):
        client = self.create_client(self.presentation['root'],
                                    self.presentation['media'],
                                    self.presentation['config'])

        with client.get('/') as response:
            self.assertEqual(response.status, '200 OK')

    def test_get_img_view_status(self):
        client = self.create_client(self.presentation['root'],
                                    self.presentation['media'],
                                    self.presentation['config'])
        url = '/img/{0}'.format(self.presentation['image'])

        with client.get(url) as response:
            self.assertEqual(response.status, '200 OK')

    def test_load_markdown_slides(self):
        slides = load_markdown_slides(self.presentation['root'])

        self.assertEqual(slides, self.slides)
