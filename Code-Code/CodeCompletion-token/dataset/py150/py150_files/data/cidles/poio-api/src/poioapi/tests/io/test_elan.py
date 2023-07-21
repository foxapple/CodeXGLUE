# -*- coding: utf-8 -*-
#
# Poio Tools for Linguists
#
# Copyright (C) 2009-2013 Poio Project
# Author: António Lopes <alopes@cidles.eu>
# URL: <http://media.cidles.eu/poio/>
# For license information, see LICENSE.TXT

import os

import poioapi.io.elan
import poioapi.io.graf

class TestElan:
    """
    This class contain the test methods to the
    class io.elan.py.

    """

    def setup(self):
        self.filename = os.path.join(os.path.dirname(__file__), "..", "sample_files",
            "elan_graf", "example.eaf")

        self.basedirname = os.path.dirname(self.filename)

        self.metafile = os.path.join(os.path.dirname(__file__), "..", "sample_files",
            "elan_graf", "example-extinfo.xml")

        self.elan = poioapi.io.elan.Parser(self.filename)

    def test_get_root_tiers(self):
        root_tiers = self.elan.get_root_tiers()

        assert len(root_tiers) == 4

    def test_get_child_tiers_for_tier(self):
        # Get the root tiers
        root_tiers = self.elan.get_root_tiers()

        # Select the W-Spch tier
        tier = root_tiers[1]

        child_tier = self.elan.get_child_tiers_for_tier(tier)

        assert len(child_tier) == 2

    def test_get_annotations_for_tier(self):
        root_tier = self.elan.get_root_tiers()[1] # W-Spch
        root_tier_annotations = self.elan.get_annotations_for_tier(root_tier)
        assert len(root_tier_annotations) == 15

        annotation = root_tier_annotations[0] # a8
        child_tier = self.elan.get_child_tiers_for_tier(root_tier)[0] # W-Words
        child_tier_annotations = self.elan.get_annotations_for_tier(child_tier, annotation)
        assert len(child_tier_annotations) == 12


    def test_get_annotations_for_tier_with_parent(self):
        root_tiers = self.elan.get_root_tiers()

        child_tiers = self.elan.get_child_tiers_for_tier(root_tiers[1])

        parent_annotation = poioapi.io.graf.Annotation('a8', 'ann_value')

        child_tier_annotations = self.elan.get_annotations_for_tier(child_tiers[1], parent_annotation)

        assert len(child_tier_annotations) == 1
        assert child_tier_annotations[0].id == "a217"

    def test_tier_has_regions(self):
        root_tiers = self.elan.get_root_tiers()

        child_tiers = self.elan.get_child_tiers_for_tier(root_tiers[1])

        tier = child_tiers[0] # W-Words

        has_regions = self.elan.tier_has_regions(tier)

        assert has_regions == True

    def test_region_for_annotation(self):
        root_tier = self.elan.get_root_tiers()[1] # W-Spch
        root_tier_annotations = self.elan.get_annotations_for_tier(root_tier)

        annotation = root_tier_annotations[0]

        regions = self.elan.region_for_annotation(annotation)

        expected_regions = (780, 4090)

        assert regions == expected_regions

    def test__annotation_for_region(self):
        annotation = self.elan._annotation_for_region("W-Spch", 780, 1340)
        assert annotation.attrib["ANNOTATION_ID"] == "a8"