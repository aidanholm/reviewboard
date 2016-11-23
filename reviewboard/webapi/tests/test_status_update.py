from __future__ import unicode_literals

from django.utils import six
from djblets.features.testing import override_feature_checks
from djblets.webapi.errors import DOES_NOT_EXIST, INVALID_FORM_DATA
from djblets.webapi.testing.decorators import webapi_test_template

from reviewboard.reviews.models.status_update import StatusUpdate
from reviewboard.webapi.resources import resources
from reviewboard.webapi.tests.base import BaseWebAPITestCase
from reviewboard.webapi.tests.mimetypes import (status_update_item_mimetype,
                                                status_update_list_mimetype)
from reviewboard.webapi.tests.mixins import (BasicTestsMetaclass,
                                             ReviewRequestChildItemMixin,
                                             ReviewRequestChildListMixin)
from reviewboard.webapi.tests.mixins_extra_data import (ExtraDataItemMixin,
                                                        ExtraDataListMixin)
from reviewboard.webapi.tests.urls import (get_review_item_url,
                                           get_status_update_item_url,
                                           get_status_update_list_url)


@six.add_metaclass(BasicTestsMetaclass)
class ResourceListTests(ExtraDataListMixin, ReviewRequestChildListMixin,
                        BaseWebAPITestCase):
    """Testing the StatusUpdateResource list APIs."""

    fixtures = ['test_users']
    resource = resources.status_update

    sample_api_url = '/review-requests/<id>/status-updates/'

    def setup_review_request_child_test(self, review_request):
        return (get_status_update_list_url(review_request),
                status_update_list_mimetype)

    def compare_item(self, item_rsp, status_update):
        self.assertEqual(item_rsp['id'], status_update.pk)
        self.assertEqual(item_rsp['summary'], status_update.summary)
        self.assertEqual(item_rsp['description'], status_update.description)
        self.assertEqual(item_rsp['url'], status_update.url)
        self.assertEqual(item_rsp['url_text'], status_update.url_text)
        self.assertEqual(item_rsp['extra_data'], status_update.extra_data)

    #
    # HTTP GET tests
    #

    def setup_basic_get_test(self, user, with_local_site, local_site_name,
                             populate_items):
        review_request = self.create_review_request(
            with_local_site=with_local_site,
            submitter=user,
            publish=True)

        if populate_items:
            items = [self.create_status_update(review_request)]
        else:
            items = []

        return (get_status_update_list_url(review_request, local_site_name),
                status_update_list_mimetype,
                items)

    #
    # HTTP POST tests
    #

    def setup_basic_post_test(self, user, with_local_site, local_site_name,
                              post_valid_data):
        review_request = self.create_review_request(
            with_local_site=with_local_site,
            submitter=user,
            publish=True)

        if post_valid_data:
            post_data = {
                'service_id': 'Service',
                'summary': 'Summary',
            }
        else:
            post_data = {}

        return (
            get_status_update_list_url(review_request, local_site_name),
            status_update_item_mimetype,
            post_data,
            [review_request])

    def check_post_result(self, user, rsp, review_request):
        status_update = StatusUpdate.objects.get(pk=rsp['status_update']['id'])
        self.compare_item(rsp['status_update'], status_update)

    @webapi_test_template
    def test_post_with_invalid_state(self):
        """Testing the POST <URL> API with an invalid state"""
        review_request = self.create_review_request(publish=True)

        with override_feature_checks(self.override_features):
            rsp = self.api_post(
                get_status_update_list_url(review_request),
                {
                    'service_id': 'Service',
                    'summary': 'Summary',
                    'state': 'incorrect',
                },
                expected_status=400)

        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], INVALID_FORM_DATA.code)
        self.assertTrue('state' in rsp['fields'])

    @webapi_test_template
    def test_post_with_invalid_change_id(self):
        """Testing the POST <URL> API with an change_id state"""
        review_request = self.create_review_request(publish=True)

        with override_feature_checks(self.override_features):
            rsp = self.api_post(
                get_status_update_list_url(review_request),
                {
                    'service_id': 'Service',
                    'summary': 'Summary',
                    'change_id': '123456',
                },
                expected_status=400)

        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], INVALID_FORM_DATA.code)
        self.assertTrue('change_id' in rsp['fields'])

    @webapi_test_template
    def test_post_with_invalid_review_id(self):
        """Testing the POST <URL> API with an invalid review_id"""
        review_request = self.create_review_request(publish=True)

        with override_feature_checks(self.override_features):
            rsp = self.api_post(
                get_status_update_list_url(review_request),
                {
                    'service_id': 'Service',
                    'summary': 'Summary',
                    'review_id': '123456',
                },
                expected_status=400)

        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], INVALID_FORM_DATA.code)
        self.assertTrue('review_id' in rsp['fields'])


@six.add_metaclass(BasicTestsMetaclass)
class ResourceItemTests(ReviewRequestChildItemMixin, ExtraDataItemMixin,
                        BaseWebAPITestCase):
    """Testing the StatusUpdateResource item APIs."""

    fixtures = ['test_users']
    sample_api_url = 'review-requests/<id>/status-updates/<id>/'
    resource = resources.status_update

    def setup_review_request_child_test(self, review_request):
        status_update = self.create_status_update(review_request)

        return (get_status_update_item_url(review_request, status_update.pk),
                status_update_item_mimetype)

    def compare_item(self, item_rsp, status_update):
        self.assertEqual(item_rsp['id'], status_update.pk)

        if status_update.review_id:
            review_request = status_update.review_request
            local_site_name = (review_request.local_site and
                               review_request.local_site.name)

            review_url = self.base_url + get_review_item_url(
                review_request, status_update.review_id, local_site_name)

            self.assertEqual(item_rsp['links']['review']['href'], review_url)

    #
    # HTTP DELETE tests
    #

    def setup_basic_delete_test(self, user, with_local_site, local_site_name):
        review_request = self.create_review_request(
            with_local_site=with_local_site,
            submitter=user,
            publish=True)
        status_update = self.create_status_update(review_request, user=user)

        return (get_status_update_item_url(review_request, status_update.pk,
                                           local_site_name),
                [status_update, review_request])

    def check_delete_result(self, user, status_update, review_request):
        self.assertNotIn(status_update, review_request.status_updates.all())

    @webapi_test_template
    def test_delete_with_does_not_exist(self):
        """Testing the DELETE <URL> API
        with Does Not Exist error
        """
        review_request = self.create_review_request(publish=True)

        with override_feature_checks(self.override_features):
            rsp = self.api_delete(
                get_status_update_item_url(review_request, 12345),
                expected_status=404)

        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], DOES_NOT_EXIST.code)

    #
    # HTTP GET tests
    #

    def setup_basic_get_test(self, user, with_local_site, local_site_name):
        review_request = self.create_review_request(
            with_local_site=with_local_site,
            submitter=user,
            publish=True)
        status_update = self.create_status_update(review_request, user=user)

        return (get_status_update_item_url(review_request, status_update.pk,
                                           local_site_name),
                status_update_item_mimetype,
                status_update)

    @webapi_test_template
    def test_get_not_modified(self):
        """Testing the GET <URL> API
        with Not Modified response
        """
        review_request = self.create_review_request(publish=True)
        status_update = self.create_status_update(review_request)

        with override_feature_checks(self.override_features):
            self._testHttpCaching(
                get_status_update_item_url(review_request, status_update.pk),
                check_etags=True)

    #
    # HTTP PUT tests
    #

    def setup_basic_put_test(self, user, with_local_site, local_site_name,
                             put_valid_data):
        review_request = self.create_review_request(
            with_local_site=with_local_site,
            submitter=user,
            publish=True)
        review = self.create_review(review_request=review_request)
        status_update = self.create_status_update(review_request, user=user)

        return (
            get_status_update_item_url(review_request, status_update.pk,
                                       local_site_name),
            status_update_item_mimetype,
            {
                'summary': 'New summary',
                'review_id': review.pk,
            },
            status_update,
            [])

    def check_put_result(self, user, item_rsp, status_update, *args):
        self.assertEqual(item_rsp['id'], status_update.pk)

        status_update = StatusUpdate.objects.get(pk=status_update.pk)
        self.compare_item(item_rsp, status_update)