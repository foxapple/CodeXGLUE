from tastypie import http
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
# from tastypie.authorization import  Authorization
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.resources import ModelResource

from django.http import HttpResponse

from .core.models import ApiKey

import logging
logger = logging.getLogger("moztrap.model.mtapi")


class MTApiKeyAuthentication(ApiKeyAuthentication):
    """Authentication that requires our custom api key implementation."""

    def get_key(self, user, api_key):
        try:
            ApiKey.objects.get(owner=user, key=api_key, active=True)
            logger.debug("api key is authorized")
        except Exception as e:
            logger.debug("api key is NOT authorized\n%s" % e)
            return self._unauthorized()

        return True


    def is_authenticated(self, request, **kwargs):
        """
        Finds the user and checks their API key. GET requests are always
        allowed.

        This overrides Tastypie's default impl, because we use a User
        proxy class, which Tastypie doesn't find

        Should return either ``True`` if allowed, ``False`` if not or an
        ``HttpResponse`` if you need something custom.
        """
        if request.method == "GET":
            return True

        from .core.auth import User

        username = request.GET.get("username") or request.POST.get("username")
        api_key = request.GET.get("api_key") or request.POST.get("api_key")

        if not username or not api_key:
            if not username:  # pragma: no cover
                logger.debug("no username")  # pragma: no cover
            elif not api_key:  # pragma: no cover
                logger.debug("no api key")  # pragma: no cover
            return self._unauthorized()

        try:
            user = User.objects.get(username=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            logger.debug("user retrieval error")
            return self._unauthorized()

        request.user = user
        return self.get_key(user, api_key)


class MTAuthorization(DjangoAuthorization):
    """Authorization that allows any user to GET but only users with permissions
    to modify.

    For the methods in here, the parent super().some_method will
    check the permission:

      APP.add_THING

    (for example).

    But we also want to say it's ok if you have the permission:

      APP.manage_THINGs

    Basically, the purpose of this class is to go beyond that you have
    to have the "add_THING" or "change_THING" or "delete_THING" and also
    that it's ok that have the "manage_THINGs" permission.
    """

    @property
    def permission(self):
        """This permission should be checked by is_authorized."""
        klass = self.resource_meta.object_class
        permission = "%s.manage_%ss" % (klass._meta.app_label,
            klass._meta.module_name)
        logger.debug("desired permission %s" % permission)
        return permission

    def read_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)
        if klass and bundle.request.user.has_perm(self.permission):
            return True
        return super(MTAuthorization, self).read_detail(object_list, bundle)

    def create_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)
        if klass and bundle.request.user.has_perm(self.permission):
            return True
        return super(MTAuthorization, self).create_detail(object_list, bundle)

    def update_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)
        if klass and bundle.request.user.has_perm(self.permission):
            return True
        return super(MTAuthorization, self).update_detail(object_list, bundle)

    def delete_detail(self, object_list, bundle):
        klass = self.base_checks(bundle.request, bundle.obj.__class__)
        if klass and bundle.request.user.has_perm(self.permission):
            return True
        return super(MTAuthorization, self).delete_detail(object_list, bundle)



class MTResource(ModelResource):
    """Implement the common code needed for CRUD API interfaces.

    Child classes must implement the following abstract methods:

    - model (property)

    """

    class Meta:
        list_allowed_methods = ["get", "post"]
        detail_allowed_methods = ["get", "put", "delete"]
        authentication = MTApiKeyAuthentication()
        authorization = MTAuthorization()
        # authorization = DjangoAuthorization()
        always_return_data = True
        ordering = ['id']

    @property
    def model(self):
        """Model class related to this resource."""
        raise NotImplementedError  # pragma: no cover


    @property
    def read_create_fields(self):
        """List of fields that are required for create but read-only for update."""
        return []


    def check_read_create(self, bundle):
        """Verify that request isn't trying to change a read-create field."""
        obj = self.get_via_uri(bundle.request.path, request=bundle.request)
        for fk in self.read_create_fields:

            if fk not in bundle.data:
                continue

            new_fk_id = self._id_from_uri(bundle.data[fk])
            old_fk_id = str(getattr(obj, fk).id)
            if new_fk_id != old_fk_id:
                error_message = str(
                    "%s of an existing %s " % (fk, self._meta.resource_name) +
                    "may not be changed.")
                logger.error(
                    "\n".join([error_message, "old: %s, new: %s"]),
                    old_fk_id, new_fk_id)
                raise ImmediateHttpResponse(
                    response=http.HttpBadRequest(error_message))

        return bundle


    def obj_create(self, bundle, request=None, **kwargs):
        """Set the created_by field for the object to the request's user"""
        request = request or bundle.request
        # this try/except logging is more helpful than 500 / 404 errors on
        # the client side
        try:
            bundle = super(MTResource, self).obj_create(
                bundle=bundle, request=request, **kwargs)
            bundle.obj.created_by = request.user
            bundle.obj.save(user=request.user)
            return bundle
        except Exception:  # pragma: no cover
            logger.exception("error creating %s", bundle)  # pragma: no cover
            raise  # pragma: no cover


    def obj_update(self, bundle, request=None, **kwargs):
        """Set the modified_by field for the object to the request's user"""
        # this try/except logging is more helpful than 500 / 404 errors on the
        # client side
        bundle = self.check_read_create(bundle)
        request = request or bundle.request
        try:
            bundle = super(MTResource, self).obj_update(
                bundle, **kwargs)
            bundle.obj.save(user=request.user)
            return bundle
        except Exception:  # pragma: no cover
            logger.exception("error updating %s", bundle)  # pragma: no cover
            raise  # pragma: no cover


    def obj_delete(self, bundle, request=None, **kwargs):
        """Delete the object.
        The DELETE request may include permanent=True/False in its params
        parameter (ie, along with the user's credentials). Default is False.
        """
        # this try/except logging is more helpful than 500 / 404 errors on
        # the client side
        request = request or bundle.request

        try:
            permanent = request.REQUEST.get('permanent', False)
            # permanent = request._request.dicts[1].get("permanent", False)
            # pull the id out of the request's path
            obj_id = self._id_from_uri(request.path)
            obj = self.model.objects.get(id=obj_id)
            bundle.obj = obj
            self.authorized_delete_detail([obj], bundle)
            obj.delete(user=request.user, permanent=permanent)
        except Exception:  # pragma: no cover
            logger.exception("error deleting %s", request.path)  # pragma: no cover
            raise


    def delete_detail(self, request, **kwargs):
        """Avoid the following error:
        WSGIWarning: Content-Type header found in a 204 response, which not
        return content.
        """
        res = super(MTResource, self).delete_detail(request, **kwargs)
        # FIXME: By TastyPie default, DELETE returns 204 No Content
        # But message_ui middleware has problem with response with no
        # content-type.
        # Replace the rest of the method with these after message_ui updated:
        #    del(res._headers["content-type"])
        #    return res
        if (res.status_code == 204):
            return HttpResponse()
        else:
            return res


    def save_related(self, bundle):
        """keep it from throwing a ConcurrencyError on obj_update"""
        super(MTResource, self).save_related(bundle)
        if bundle.request.META['REQUEST_METHOD'] == 'PUT':
            bundle.obj.cc_version = self.model.objects.get(
                id=bundle.obj.id).cc_version

    def _id_from_uri(self, uri):
        return uri.split('/')[-2]
