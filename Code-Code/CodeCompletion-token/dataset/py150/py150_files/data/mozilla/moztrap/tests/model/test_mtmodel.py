"""
Tests for ``MTModel`` and related classes.

These tests use the ``Product`` model (and ``Suite`` for cascade-delete tests),
as its a simple model inherited from ``MTModel``, and this avoids the need for
a test-only model.

"""
import datetime

from mock import patch

from tests import case



class MTModelTestCase(case.DBTestCase):
    """Common base class for MTModel tests."""
    def setUp(self):
        """Creates ``self.user`` for use by all tests."""
        self.user = self.F.UserFactory.create()



class UserDeleteTest(MTModelTestCase):
    """Tests for deleting users, and the effect on MTModels."""
    def test_delete_created_by_sets_null(self):
        """Deleting the created_by user sets created_by to None."""
        u = self.F.UserFactory()
        p = self.F.ProductFactory(user=u)

        u.delete()

        self.assertEqual(self.refresh(p).created_by, None)


    def test_delete_modified_by_sets_null(self):
        """Deleting the modified_by user sets modified_by to None."""
        p = self.F.ProductFactory()
        u = self.F.UserFactory()
        p.save(user=u)

        u.delete()

        self.assertEqual(self.refresh(p).modified_by, None)


    def test_delete_deleted_by_sets_null(self):
        """Deleting the deleted_by user sets deleted_by to None."""
        p = self.F.ProductFactory()
        u = self.F.UserFactory()
        p.delete(user=u)

        u.delete()

        self.assertEqual(self.refresh(p).deleted_by, None)



class MTModelMockNowTestCase(MTModelTestCase):
    """Base class for MTModel tests that need "now" mocked."""
    def setUp(self):
        """Mocks datetime.utcnow() with datetime in self.utcnow."""
        super(MTModelMockNowTestCase, self).setUp()

        self.utcnow = datetime.datetime(2011, 12, 13, 22, 39)
        patcher = patch("moztrap.model.mtmodel.datetime")
        self.mock_utcnow = patcher.start().datetime.utcnow
        self.mock_utcnow.return_value = self.utcnow
        self.addCleanup(patcher.stop)



class CreateTest(MTModelMockNowTestCase):
    """Tests for (created/modified)_(on/by) when using Model.objects.create."""
    def test_created_by_none(self):
        """If ``user`` is not given to create(), created_by is None."""
        p = self.model.Product.objects.create(name="Foo")

        self.assertEqual(p.created_by, None)


    def test_created_by(self):
        """If ``user`` is given to create(), created_by is set."""
        p = self.model.Product.objects.create(name="Foo", user=self.user)

        self.assertEqual(p.created_by, self.user)


    def test_new_modified_by_none(self):
        """If ``user`` is not given to create(), modified_by is None."""
        p = self.model.Product.objects.create(name="Foo")

        self.assertEqual(p.modified_by, None)


    def test_new_modified_by(self):
        """If ``user`` is given to create(), modified_by is set."""
        p = self.model.Product.objects.create(name="Foo", user=self.user)

        self.assertEqual(p.modified_by, self.user)


    def test_created_on(self):
        """create() method sets created_on."""
        p = self.model.Product.objects.create(name="Foo")

        self.assertEqual(p.created_on, self.utcnow)


    def test_new_modified_on(self):
        """create() method sets modified_on."""
        p = self.model.Product.objects.create(name="Foo")

        self.assertEqual(p.modified_on, self.utcnow)



class SaveTest(MTModelMockNowTestCase):
    """Tests for (created/modified)_(on/by) when using instance.save."""
    def test_created_by_none(self):
        """If ``user`` is not given to new obj save(), created_by is None."""
        p = self.model.Product(name="Foo")
        p.save()

        self.assertEqual(p.created_by, None)


    def test_created_by(self):
        """If ``user`` is given to new obj save(), created_by is set."""
        p = self.model.Product(name="Foo")
        p.save(user=self.user)

        self.assertEqual(p.created_by, self.user)


    def test_new_modified_by_none(self):
        """If ``user`` is not given to new obj save(), modified_by is None."""
        p = self.model.Product(name="Foo")
        p.save()

        self.assertEqual(p.modified_by, None)


    def test_new_modified_by(self):
        """If ``user`` is given to new obj save(), modified_by is set."""
        p = self.model.Product(name="Foo")
        p.save(user=self.user)

        self.assertEqual(p.modified_by, self.user)


    def test_created_on(self):
        """save() method sets created_on."""
        p = self.model.Product(name="Foo")
        p.save()

        self.assertEqual(p.created_on, self.utcnow)


    def test_new_modified_on(self):
        """save() method sets modified_on for new object."""
        p = self.model.Product(name="Foo")
        p.save()

        self.assertEqual(p.modified_on, self.utcnow)


    def test_modified_by_none(self):
        """If ``user`` is not given to save(), modified_by is set to None."""
        p = self.model.Product.objects.create(name="Foo", user=self.user)
        p.save()

        self.assertEqual(p.modified_by, None)


    def test_modified_by(self):
        """If ``user`` is given to save(), modified_by is set."""
        p = self.model.Product.objects.create(name="Foo")
        p.save(user=self.user)

        self.assertEqual(p.modified_by, self.user)


    def test_modified_on(self):
        """save() method sets modified_on for existing object."""
        p = self.model.Product.objects.create(name="Foo")
        new_now = datetime.datetime(2012, 1, 1, 12, 0)
        self.mock_utcnow.return_value = new_now
        p.save()

        self.assertEqual(p.modified_on, new_now)


    def test_notrack_modified_on(self):
        """If notrack=True, doesn't update modified_on."""
        self.mock_utcnow.return_value = datetime.datetime(2012, 1, 1)
        p = self.model.Product.objects.create(name="Foo")

        self.mock_utcnow.return_value = datetime.datetime(2012, 1, 2)
        p.save(notrack=True)

        self.assertEqual(
            self.refresh(p).modified_on, datetime.datetime(2012, 1, 1))


    def test_notrack_modified_by(self):
        """If notrack=True, doesn't update modified_by."""
        p = self.model.Product.objects.create(name="Foo", user=self.user)

        p.save(notrack=True)

        self.assertEqual(self.refresh(p).modified_by, self.user)



class UpdateTest(MTModelMockNowTestCase):
    """Tests for modified_(by/on) when using queryset.update."""
    def test_modified_by_none(self):
        """queryset update() sets modified_by to None if not given user."""
        p = self.model.Product.objects.create(name="Foo", user=self.user)

        self.model.Product.objects.update(name="Bar")

        self.assertEqual(self.refresh(p).modified_by, None)


    def test_modified_by(self):
        """queryset update() sets modified_by if given user."""
        p = self.model.Product.objects.create(name="Foo")

        self.model.Product.objects.update(name="Bar", user=self.user)

        self.assertEqual(self.refresh(p).modified_by, self.user)


    def test_modified_on(self):
        """queryset update() sets modified_on."""
        p = self.model.Product.objects.create(name="Foo")
        new_now = datetime.datetime(2012, 1, 1, 12, 0)
        self.mock_utcnow.return_value = new_now

        self.model.Product.objects.update(name="Bar")

        self.assertEqual(self.refresh(p).modified_on, new_now)


    def test_notrack_modified_on(self):
        """If notrack=True, doesn't update modified_on."""
        self.mock_utcnow.return_value = datetime.datetime(2012, 1, 1)
        p = self.model.Product.objects.create(name="Foo")

        self.mock_utcnow.return_value = datetime.datetime(2012, 1, 2)
        self.model.Product.objects.update(name="bar", notrack=True)

        self.assertEqual(self.refresh(p).modified_on, datetime.datetime(2012, 1, 1))


    def test_notrack_modified_by(self):
        """If notrack=True, doesn't update modified_by."""
        p = self.model.Product.objects.create(name="Foo", user=self.user)

        self.model.Product.objects.update(name="bar", notrack=True)

        self.assertEqual(self.refresh(p).modified_by, self.user)



class DeleteTest(MTModelMockNowTestCase):
    """Tests for deleted_(by/on) when using instance.delete or qs.delete."""
    def test_queryset_deleted_by_none(self):
        """queryset delete() sets deleted_by to None if not given user."""
        p = self.F.ProductFactory.create()

        self.model.Product.objects.all().delete()

        self.assertEqual(self.refresh(p).deleted_by, None)


    def test_queryset_deleted_by(self):
        """queryset delete() sets deleted_by if given user."""
        p = self.F.ProductFactory.create()

        self.model.Product.objects.all().delete(user=self.user)

        self.assertEqual(self.refresh(p).deleted_by, self.user)


    def test_queryset_deleted_on(self):
        """queryset delete() sets deleted_on."""
        p = self.F.ProductFactory.create()

        self.model.Product.objects.all().delete()

        self.assertEqual(self.refresh(p).deleted_on, self.utcnow)


    def test_deleted_by_none(self):
        """delete() sets deleted_by to None if not given user."""
        p = self.F.ProductFactory.create()

        p.delete()

        self.assertEqual(self.refresh(p).deleted_by, None)


    def test_deleted_by(self):
        """delete() sets deleted_by if given user."""
        p = self.F.ProductFactory.create()

        p.delete(user=self.user)

        self.assertEqual(self.refresh(p).deleted_by, self.user)


    def test_deleted_on(self):
        """delete() sets deleted_on."""
        p = self.F.ProductFactory.create()

        p.delete()

        self.assertEqual(self.refresh(p).deleted_on, self.utcnow)



class HardDeleteTest(case.DBTestCase):
    """Tests for deletion with permanent=True."""
    def test_instance(self):
        """Can hard-delete an instance with permanent=True."""
        p = self.F.ProductFactory.create()

        p.delete(permanent=True)

        self.assertEqual(self.model.Product._base_manager.count(), 0)


    def test_queryset(self):
        """Can hard-delete a queryset with permanent=True."""
        self.F.ProductFactory.create()

        self.model.Product.objects.all().delete(permanent=True)

        self.assertEqual(self.model.Product._base_manager.count(), 0)



class CascadeDeleteTest(MTModelTestCase):
    """Tests for cascading soft-delete."""
    def test_queryset_deleted_by_none(self):
        """queryset delete() sets deleted_by None if no user on cascade."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)

        self.model.Product.objects.all().delete()

        self.assertEqual(self.refresh(s).deleted_by, None)


    def test_queryset_deleted_by(self):
        """queryset delete() sets deleted_by to given user on cascade."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)

        self.model.Product.objects.all().delete(user=self.user)

        self.assertEqual(self.refresh(s).deleted_by, self.user)


    def test_queryset_deleted_on(self):
        """qs delete() sets deleted_on to same time as parent on cascade."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)

        self.model.Product.objects.all().delete()

        p = self.refresh(p)
        s = self.refresh(s)
        self.assertIsNot(p.deleted_on, None)

        self.assertEqual(s.deleted_on, p.deleted_on)


    def test_deleted_by_none(self):
        """delete() sets deleted_by None if no user on cascade."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)

        p.delete()

        self.assertEqual(self.refresh(s).deleted_by, None)


    def test_deleted_by(self):
        """delete() sets deleted_by to given user on cascade."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)

        p.delete(user=self.user)

        self.assertEqual(self.refresh(s).deleted_by, self.user)


    def test_deleted_on(self):
        """delete() sets deleted_on to same time as parent on cascade."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)

        p.delete()

        p = self.refresh(p)
        s = self.refresh(s)
        self.assertIsNot(p.deleted_on, None)

        self.assertEqual(s.deleted_on, p.deleted_on)


    def test_no_cascade_redelete(self):
        """cascade delete won't update deleted-on for previously deleted."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)
        # need to patch utcnow because MySQL doesn't give us better than
        # one-second resolution on datetimes.
        with patch("moztrap.model.mtmodel.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(
                2011, 12, 13, 10, 23, 58)
            s.delete()
            # ... a day later...
            mock_dt.datetime.utcnow.return_value = datetime.datetime(
                2011, 12, 14, 9, 18, 22)
            p.delete()

        self.assertNotEqual(
            self.refresh(s).deleted_on, self.refresh(p).deleted_on)



class UndeleteMixin(object):
    """Utility assertions mixin for undelete tests."""
    def assertNotDeleted(self, obj):
        self.assertEqual(obj.deleted_on, None)
        self.assertEqual(obj.deleted_by, None)



class UndeleteTest(UndeleteMixin, MTModelTestCase):
    """Tests for undelete using instance.undelete or qs.undelete."""
    def test_instance(self):
        """instance.undelete() undeletes an instance."""
        p = self.F.ProductFactory.create()
        p.delete()

        p.undelete()

        self.assertNotDeleted(p)


    def test_queryset(self):
        """qs.undelete() undeletes all objects in the queryset."""
        p = self.F.ProductFactory.create()
        p.delete()

        self.model.Product.everything.all().undelete()

        self.assertNotDeleted(self.refresh(p))



class CascadeUndeleteTest(UndeleteMixin, MTModelTestCase):
    """Tests for cascading undelete."""
    def test_instance(self):
        """Undeleting an instance also undeletes cascade-deleted dependents."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)
        p.delete()
        p = self.refresh(p)

        p.undelete()

        self.assertNotDeleted(self.refresh(s))


    def test_queryset(self):
        """Undeleting a queryset also undeletes cascade-deleted dependents."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)
        p.delete()

        self.model.Product.everything.all().undelete()

        self.assertNotDeleted(self.refresh(s))


    def test_cascade_limited(self):
        """Undelete only cascades to objs cascade-deleted with that object."""
        p = self.F.ProductFactory.create()
        s = self.F.SuiteFactory.create(product=p)
        # need to patch utcnow because MySQL doesn't give us better than
        # one-second resolution on datetimes.
        with patch("moztrap.model.mtmodel.datetime") as mock_dt:
            mock_dt.datetime.utcnow.return_value = datetime.datetime(
                2011, 12, 13, 10, 23, 58)
            s.delete()
            # ... a day later ...
            mock_dt.datetime.utcnow.return_value = datetime.datetime(
                2011, 12, 14, 9, 18, 22)
            p.delete()

        self.refresh(p).undelete()

        self.assertIsNot(self.refresh(s).deleted_on, None)



class CloneTest(UndeleteMixin, MTModelTestCase):
    """Tests for cloning."""
    def test_cascade_non_m2m_or_reverse_fk(self):
        """Cascade-cloning an attr that isn't M2M or rev FK raises an error."""
        p = self.F.ProductFactory.create()
        with self.assertRaises(ValueError):
            p.clone(cascade=["name"])


    @patch("moztrap.model.mtmodel.datetime")
    def test_updates_created_on(self, mock_dt):
        """Cloned objects get a new created-on timestamp."""
        mock_dt.datetime.utcnow.return_value = datetime.datetime(
            2012, 1, 30)
        p = self.F.ProductFactory.create()

        cloned_on = datetime.datetime(2012, 1, 31)
        mock_dt.datetime.utcnow.return_value = cloned_on
        new = p.clone()

        self.assertEqual(new.created_on, cloned_on)


    def test_updates_created_by(self):
        """Cloned objects get a new created-by; the cloning user."""
        u1 = self.F.UserFactory.create()
        p = self.F.ProductFactory.create(user=u1)

        u2 = self.F.UserFactory.create()
        new = p.clone(user=u2)

        self.assertEqual(new.created_by, u2)


    @patch("moztrap.model.mtmodel.datetime")
    def test_updates_modified_on(self, mock_dt):
        """Cloned objects get a new modified-on timestamp."""
        mock_dt.datetime.utcnow.return_value = datetime.datetime(
            2012, 1, 30)
        p = self.F.ProductFactory.create()

        cloned_on = datetime.datetime(2012, 1, 31)
        mock_dt.datetime.utcnow.return_value = cloned_on
        new = p.clone()

        self.assertEqual(new.modified_on, cloned_on)


    def test_updates_modified_by(self):
        """Cloned objects get a new modified-by; the cloning user."""
        u1 = self.F.UserFactory.create()
        p = self.F.ProductFactory.create(user=u1)

        u2 = self.F.UserFactory.create()
        new = p.clone(user=u2)

        self.assertEqual(new.modified_by, u2)



class MTManagerTest(MTModelTestCase):
    """Tests for MTManager."""
    def test_objects_doesnt_include_deleted(self):
        """``objects`` manager doesn't include deleted objects."""
        p1 = self.F.ProductFactory.create()
        p2 = self.F.ProductFactory.create()
        p2.delete()

        self.assertEqual(set(self.model.Product.objects.all()), set([p1]))


    def test_everything_does_include_deleted(self):
        """``everything`` manager does include deleted objects."""
        p1 = self.F.ProductFactory.create()
        p2 = self.F.ProductFactory.create()
        p2.delete()

        self.assertEqual(
            set(self.model.Product.everything.all()), set([p1, p2]))


    def test_everything_is_default_manager(self):
        """``everything`` manager is the default manager."""
        self.assertIs(
            self.model.Product._default_manager, self.model.Product.everything)


    def test_related_managers_dont_include_deleted(self):
        """Related managers don't include deleted objects."""
        pv1 = self.F.ProductVersionFactory.create(version="2.0")
        pv2 = self.F.ProductVersionFactory.create(product=pv1.product)
        pv2.delete()

        self.assertEqual(set(pv1.product.versions.all()), set([pv1]))



class TeamModelTest(case.DBTestCase):
    """Tests for TeamModel base class."""
    @property
    def TeamModel(self):
        from moztrap.model.mtmodel import TeamModel
        return TeamModel


    def test_parent(self):
        """parent property is None in base class."""
        t = self.TeamModel()
        self.assertIsNone(t.parent)



class DraftStatusModelTest(case.DBTestCase):
    """
    Tests for DraftStatusModel base class.

    The tests use Run, a DraftStatusModel subclass, to avoid the need for a
    test-only model.

    """
    def test_activate(self):
        """Test the activate method."""
        r = self.F.RunFactory.create(status="draft")

        r.activate()

        self.assertEqual(self.refresh(r).status, "active")


    def test_draft(self):
        """Test the draft method."""
        r = self.F.RunFactory.create(status="active")

        r.draft()

        self.assertEqual(self.refresh(r).status, "draft")


    def test_deactivate(self):
        """Test the deactivate method."""
        r = self.F.RunFactory.create(status="active")

        r.deactivate()

        self.assertEqual(self.refresh(r).status, "disabled")


    def test_activate_by_user(self):
        """Test the activate method with a user."""
        r = self.F.RunFactory.create(status="draft")
        u = self.F.UserFactory.create()

        r.activate(user=u)

        self.assertEqual(self.refresh(r).modified_by, u)


    def test_draft_by_user(self):
        """Test the draft method with a user."""
        r = self.F.RunFactory.create(status="active")
        u = self.F.UserFactory.create()

        r.draft(user=u)

        self.assertEqual(self.refresh(r).modified_by, u)


    def test_deactivate_by_user(self):
        """Test the deactivate method with a user."""
        r = self.F.RunFactory.create(status="active")
        u = self.F.UserFactory.create()

        r.deactivate(user=u)

        self.assertEqual(self.refresh(r).modified_by, u)



class NotDeletedCountTest(case.DBTestCase):
    """Tests for NotDeletedCount aggregate."""
    @property
    def NotDeletedCount(self):
        """The aggregate class under test."""
        from moztrap.model.mtmodel import NotDeletedCount
        return NotDeletedCount


    def test_counts_not_deleted(self):
        """Counts only not-deleted related objects."""
        pv = self.F.ProductVersionFactory.create()
        self.F.ProductVersionFactory.create(product=pv.product)
        pv.delete()

        p = self.model.Product.objects.annotate(
            num_versions=self.NotDeletedCount("versions")).get()

        self.assertEqual(p.num_versions, 1)


    def test_aggregate_annotation(self):
        """
        Works when aggregating over an annotation.

        This is a bit of an artificially-constructed test in order to cover a
        certain edge case in the aggregation code.

        """
        from django.db.models import Count

        pv1 = self.F.ProductVersionFactory.create()
        self.F.ProductVersionFactory.create()
        pv1.product.delete()

        # In this case we are intentionally selecting all products, and
        # counting all versions (even deleted ones) in the initial num_versions
        # annotation. What we want to test is that the final aggregation counts
        # only not-deleted products.
        res = self.model.Product.everything.annotate(
            num_versions=Count("versions")).aggregate(
            products_with_versions=self.NotDeletedCount("num_versions"))

        self.assertEqual(res, {"products_with_versions": 1})



class OptimisticLockingTest(case.DBTestCase):
    """Test optimistic locking to avoid silent overwrite on concurrent edits."""
    def test_concurrency_error(self):
        """Save raises ConcurrencyError if version does not match the DB."""
        p = self.F.ProductFactory()

        p2 = self.model.Product.objects.get()
        p2.name = "Name One"
        p2.save()

        p.name = "Name Two"

        with self.assertRaises(self.model.ConcurrencyError):
            p.save()


    def test_queryset_update_increments_version(self):
        """Update via queryset increments version in database, not just save."""
        p = self.F.ProductFactory()

        self.model.Product.objects.update(name="Name One")

        p.name = "Name Two"

        with self.assertRaises(self.model.ConcurrencyError):
            p.save()
