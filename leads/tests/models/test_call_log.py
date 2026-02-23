from django.test import TestCase
from django.contrib.auth.models import User
from ...models import City, Lead, CallLog


class CallLogModelTest(TestCase):

    def setUp(self):
        # CallLog wymaga Lead, Lead wymaga City
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_create_call_log_with_user(self):
        """Tworzy log połączenia przypisany do usera"""
        call_log = CallLog.objects.create(
            lead=self.lead,
            user=self.user,
            status=CallLog.STATUS_TALKED,
        )

        self.assertEqual(call_log.lead, self.lead)
        self.assertEqual(call_log.user, self.user)
        self.assertEqual(call_log.status, CallLog.STATUS_TALKED)

    def test_create_call_log_without_user(self):
        """Log połączenia może istnieć bez usera (user=null=True)"""
        call_log = CallLog.objects.create(
            lead=self.lead,
            user=None,
            status=CallLog.STATUS_NO_ANSWER,
        )

        self.assertIsNone(call_log.user)

    def test_call_log_default_type_is_call(self):
        """Domyślny typ logu to 'call'"""
        call_log = CallLog.objects.create(
            lead=self.lead,
            status=CallLog.STATUS_TALKED,
        )

        self.assertEqual(call_log.type, CallLog.TYPE_CALL)

    def test_call_log_default_is_reminder_inactive(self):
        """Domyślnie przypomnienie jest nieaktywne"""
        call_log = CallLog.objects.create(
            lead=self.lead,
            status=CallLog.STATUS_TALKED,
        )

        self.assertFalse(call_log.is_reminder_active)

    def test_call_log_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego logi (on_delete=CASCADE)"""
        CallLog.objects.create(
            lead=self.lead,
            status=CallLog.STATUS_TALKED,
        )

        self.lead.delete()

        self.assertEqual(CallLog.objects.count(), 0)

    def test_call_log_user_is_null_when_user_is_deleted(self):
        """Usunięcie usera ustawia user=NULL w logu (on_delete=SET_NULL)"""
        CallLog.objects.create(
            lead=self.lead,
            user=self.user,
            status=CallLog.STATUS_TALKED,
        )

        self.user.delete()

        call_log = CallLog.objects.first()
        self.assertIsNone(call_log.user)
