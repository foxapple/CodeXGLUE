from collections import Counter, namedtuple, defaultdict
import logging
import shortuuid
import datetime
import numpy

from util import cached_property
from util import dict_from_dir
from totalimpactwebapp.configs import get_genre_config
from totalimpactwebapp import json_sqlalchemy
from totalimpactwebapp import db
from totalimpactwebapp import configs


logger = logging.getLogger("ti.reference_set")
reference_set_lists = None


class ProductLevelReferenceSet(object):
    def __init__(self):
        # if reference_set_lists has never been loaded, then load it
        global reference_set_lists
        if reference_set_lists is None:
            reference_set_lists = load_all_reference_set_lists()


    def get_specific_reference_set_list(self, mendeley_discipline, provider, interaction):
        lookup_dict = dict(provider=provider, 
                    interaction=interaction, 
                    year=self.year, 
                    genre=self.genre, 
                    host=self.host, 
                    mendeley_discipline=mendeley_discipline)

        lookup_key = ReferenceSetList.build_lookup_key(**lookup_dict)

        try:
            percentile_list = reference_set_lists[lookup_key]
            return {"percentile_list": percentile_list, "mendeley_discipline": mendeley_discipline}
        except KeyError:
            return None


    def get_percentile_lookup_list(self, provider, interaction):
        global reference_set_lists
        
        if self.genre=="article":
            if self.mendeley_discipline:
                response = self.get_specific_reference_set_list(self.mendeley_discipline, provider, interaction)
                if not response:
                    # if not found, try again across all mendeley disciplines
                    response = self.get_specific_reference_set_list(u"ALL", provider, interaction)
            else:
                response = self.get_specific_reference_set_list(u"ALL", provider, interaction)
        else:
            # a few products have a mendeley discipline even though not an article
            # (some figshare posters etc added to mendeley)
            # so don't use stored mendeley discipline because won't find the right refset, use None instead
            response = self.get_specific_reference_set_list(None, provider, interaction)

        # logger.info(u"found get_percentile_lookup_list={percentile_list} for key {mendeley_discipline}".format(
        #     percentile_list=response["percentile_list"], mendeley_discipline=response["mendeley_discipline"]))

        return response


    def get_percentile(self, provider, interaction, raw_value):
        percentile_list_dict = self.get_percentile_lookup_list(provider, interaction)

        if not percentile_list_dict or not percentile_list_dict["percentile_list"]:
            return None

        percentile = 0
        for p in percentile_list_dict["percentile_list"].percentiles:
            percentile += 1
            if p >= raw_value:
                break

        if percentile >= 100:
            percentile = 99

        lookup_mendeley_discipline = percentile_list_dict["mendeley_discipline"]
        if not lookup_mendeley_discipline or lookup_mendeley_discipline==u'ALL':
            lookup_mendeley_discipline = ""

        response = {  
            "value": percentile,
            "mendeley_discipline_str": lookup_mendeley_discipline,
            "genre_plural": get_genre_config(self.genre)["plural_name"]
            }

        return response


    def to_dict(self):
        attributes_to_ignore = [
            "refset"
        ]
        ret = dict_from_dir(self, attributes_to_ignore)
        return ret



class ReferenceSetList(db.Model):
    refset_id = db.Column(db.Text, primary_key=True)
    genre = db.Column(db.Text)
    host = db.Column(db.Text)
    year = db.Column(db.Text)
    mendeley_discipline = db.Column(db.Text)
    provider = db.Column(db.Text)
    interaction = db.Column(db.Text)
    created = db.Column(db.DateTime())
    percentiles = db.Column(json_sqlalchemy.JSONAlchemy(db.Text))
    N = db.Column(db.Integer)

    def __init__(self, **kwargs):
        if not "refset_id" in kwargs:
            shortuuid.set_alphabet('abcdefghijklmnopqrstuvwxyz1234567890')
            self.refset_id = shortuuid.uuid()[0:24]

        if not "created" in kwargs:
            self.created = datetime.datetime.utcnow()
        super(ReferenceSetList, self).__init__(**kwargs)

    @classmethod
    def build_lookup_key(cls, year=None, genre=None, host=None, mendeley_discipline=None, provider=None, interaction=None):
        lookup_key = (
            year, 
            genre, 
            host, 
            mendeley_discipline,
            provider, 
            interaction, 
            )
        return lookup_key

    @classmethod
    def lookup_key_to_dict(self, metric_key):
        return dict(zip((
            "year", 
            "genre", 
            "host", 
            "mendeley_discipline", 
            "provider", 
            "interaction"
            ), metric_key))

    def get_lookup_key(self):
        return self.build_lookup_key(
            year=self.year, 
            genre=self.genre, 
            host=self.host, 
            mendeley_discipline=self.mendeley_discipline,
            provider=self.provider, 
            interaction=self.interaction, 
            )



class RefsetBuilder(object):
    def __init__(self):
        self.metric_counters = defaultdict(Counter)
        self.product_counter = Counter()

    @cached_property
    def metric_keys(self):
        return self.metric_counters.keys()

    def record_metric(self, year=None, genre=None, host=None, mendeley_discipline=None, provider=None, interaction=None, raw_value=None):
        metric_key_with_mendeley = ReferenceSetList.build_lookup_key(
            year=year, 
            genre=genre, 
            host=host, 
            mendeley_discipline=mendeley_discipline, 
            provider=provider, 
            interaction=interaction)

        self.metric_counters[metric_key_with_mendeley][raw_value] += 1

        if genre=="article":
            metric_key_all_mendeley = ReferenceSetList.build_lookup_key(
                year=year, 
                genre=genre, 
                host=host, 
                mendeley_discipline=u"ALL", 
                provider=provider, 
                interaction=interaction)

            self.metric_counters[metric_key_all_mendeley][raw_value] += 1



    def record_product(self, year=None, genre=None, host=None, mendeley_discipline=None):
        product_key_with_mendeley = ReferenceSetList.build_lookup_key(
            year=year, 
            genre=genre, 
            host=host, 
            mendeley_discipline=mendeley_discipline, 
            provider=None, 
            interaction=None)
        self.product_counter[product_key_with_mendeley] += 1

        if genre=="article":
            product_key_all_mendeley = ReferenceSetList.build_lookup_key(
                year=year, 
                genre=genre, 
                host=host, 
                mendeley_discipline=u"ALL",
                provider=None, 
                interaction=None)
            self.product_counter[product_key_all_mendeley] += 1


    def product_key_from_metric_key(self, metric_key):
        (year, genre, host, mendeley_discipline, provider, interaction) = metric_key
        product_key = ReferenceSetList.build_lookup_key(
            year=year, 
            genre=genre, 
            host=host, 
            mendeley_discipline=mendeley_discipline, 
            provider=None, 
            interaction=None)
        return product_key

    def percentiles_Ns(self, metric_key):
        elements = list(self.metric_counters[metric_key].elements())
        n_non_zero = len(elements)

        product_key = self.product_key_from_metric_key(metric_key)
        n_total = self.product_counter[product_key]

        # zero pad for all metrics except for PLOS ALM views and downloads
        if ("plosalm" in metric_key) and (("pdf_views" in metric_key) or ("html_views" in metric_key)):
            n_zero = 0
            n_total = n_non_zero
        else:
            n_zero = n_total - n_non_zero

        return {"n_total": n_total, "n_zero": n_zero}


    def percentiles(self, metric_key):
        # if fewer than 10 points, don't save percentiles
        if self.percentiles_Ns(metric_key)["n_total"] < 10:
            return None

        # expand the accumulations
        elements = list(self.metric_counters[metric_key].elements())

        # add the zeros
        n_total = self.percentiles_Ns(metric_key)["n_total"]
        n_zero = self.percentiles_Ns(metric_key)["n_zero"]

        if n_zero:
            elements += [0 for i in range(n_zero)]

        percentiles = numpy.percentile(elements, q=range(101))
        percentiles = [int(round(p, 0)) for p in percentiles]

        return percentiles
           

    def export_histograms(self):
        refset_lists = []
        for metric_key in self.metric_keys:
            percentiles = self.percentiles(metric_key)
            if percentiles:
                logger.info(u"metric_key={percentiles}".format(
                    percentiles=percentiles))
                new_refset_list = ReferenceSetList(**ReferenceSetList.lookup_key_to_dict(metric_key))
                new_refset_list.percentiles = percentiles
                new_refset_list.N = self.percentiles_Ns(metric_key)["n_total"]
                refset_lists.append(new_refset_list)
        return(refset_lists)


    @classmethod
    def export_csv_rows(cls):
        global reference_set_lists
        if not reference_set_lists:
            reference_set_lists = load_all_reference_set_lists()

        rows = []
        heading = ReferenceSetList.build_lookup_key(
                year="year", 
                genre="genre", 
                host="host", 
                mendeley_discipline="mendeley_discipline", 
                provider="provider", 
                interaction="interaction")
        heading = heading + ("percentile", "value")
        rows.append(u",".join(list(heading)))

        for refset_list_key, refset_list in reference_set_lists.iteritems():
            i = 0
            number_percentile_values = len(refset_list.percentiles) + 0.0
            for p in refset_list.percentiles:
                i += 1
                row = [column if column else "" for column in refset_list_key]
                row.append(str(int(round(100*i/number_percentile_values, 0))))
                row.append(str(p))
                rows.append(u",".join(row))
        return rows


    def process_profile(self, profile):
        logger.info(u"build_refsets: on {url_slug}".format(url_slug=profile.url_slug))

        for product in profile.products_not_removed:
            if product.biblio.display_title == "no title":
                # logger.info("no good biblio for tiid {tiid}".format(
                #     tiid=product.tiid))
                continue

            year = product.year
            try:
                year = year.replace("'", "").replace('"', '')
                if int(year[0:4]) < 2000:
                    year = "pre2000"
            except (ValueError, AttributeError):
                year = "unknown"

            self.record_product(
                year=year, 
                genre=product.genre, 
                host=product.host, 
                mendeley_discipline=product.mendeley_discipline)

            for metric in product.metrics:

                raw_value = metric.most_recent_snap.raw_value
                # only add to histogram if it is a number, not a string or mendeley dict etc
                if not isinstance(raw_value, (int, long, float)):
                    continue

                self.record_metric(
                    year=year, 
                    genre=product.genre, 
                    host=product.host, 
                    mendeley_discipline=product.mendeley_discipline, 
                    provider=metric.provider, 
                    interaction=metric.interaction, 
                    raw_value=raw_value)


def load_all_reference_set_lists():
    global reference_set_lists

    #reset it
    reference_set_lists = {}

    for refset_list_obj in ReferenceSetList.query.all():
        # we want it to persist across sessions, and is read-only, so detached from session works great
        db.session.expunge(refset_list_obj)
        lookup_key = refset_list_obj.get_lookup_key()
        reference_set_lists[lookup_key] = refset_list_obj

    logger.info(u"just loaded reference sets, n={n}".format(
        n=len(reference_set_lists)))

    return reference_set_lists



def save_all_reference_set_lists(refset_builder):
    if not refset_builder.product_counter:
        return None

    logger.info(u"removing old refsets")
    # as per http://stackoverflow.com/questions/16573802/flask-sqlalchemy-how-to-delete-all-rows-in-a-single-table
    ReferenceSetList.query.delete()
    db.session.commit()

    #add new refests
    logger.info(u"adding new reference sets")
    refset_list_objects = refset_builder.export_histograms()
    for refset_list_obj in refset_list_objects:
        db.session.add(refset_list_obj)

    db.session.commit()
    logger.info("done adding")






