""" Views
"""

from json.decoder import JSONDecodeError
import logging
import threading

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, FormView
from formtools.wizard.views import SessionWizardView

from recordtransfer.appsettings import BAG_STORAGE_FOLDER
from recordtransfer.bagger import create_bag
from recordtransfer.caais import generate_caais_tags_from_form, DocumentGenerator
from recordtransfer.models import UploadedFile, UploadSession
from recordtransfer.persistentuploadhandler import PersistentUploadedFile


LOGGER = logging.getLogger(__name__)


class Index(TemplateView):
    template_name = 'recordtransfer/home.html'


class TransferSent(TemplateView):
    template_name = 'recordtransfer/transfersent.html'


class FormPreparation(TemplateView):
    template_name = 'recordtransfer/formpreparation.html'


class TransferFormWizard(SessionWizardView):
    TEMPLATES = {
        "sourceinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Source Information",
        },
        "contactinfo": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Contact Information",
        },
        "recorddescription": {
            "templateref": "recordtransfer/standardform.html",
            "formtitle": "Record Description",
        },
        "rights": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": "Record Rights",
        },
        "otheridentifiers": {
            "templateref": "recordtransfer/formsetform.html",
            "formtitle": "Other Identifiers",
            "infomessage": (
                "This step is optional, if you do not have any other IDs associated with the "
                "records, go to the next step"
            )
        },
        "uploadfiles": {
            "templateref": "recordtransfer/dropzoneform.html",
            "formtitle": "Upload Files",
        },
    }

    def get_template_names(self):
        step_name = self.steps.current
        return [self.TEMPLATES[step_name]["templateref"]]

    def get_context_data(self, form, **kwargs):
        context = super(TransferFormWizard, self).get_context_data(form, **kwargs)
        step_name = self.steps.current
        context.update({'form_title': self.TEMPLATES[step_name]['formtitle']})
        if 'infomessage' in self.TEMPLATES[step_name]:
            context.update({'info_message': self.TEMPLATES[step_name]['infomessage']})
        return context

    def done(self, form_list, **kwargs):
        # Retrieve all of the data and files
        data = self.get_all_cleaned_data()
        upload_session_token = data['session_token']
        files = UploadedFile.objects.filter(
            session__token=upload_session_token
        ).filter(
            old_copy_removed=False
        )

        # Use data to create tag objects
        caais_tags = generate_caais_tags_from_form(data)
        doc_generator = DocumentGenerator(caais_tags)
        html_document = doc_generator.generate_html_document()
        tag_objects = [
            (caais_tags, 'yaml'),
            (html_document, 'html'),
        ]
        LOGGER.info('Generated yaml metadata and html document')

        # Create bag with uploaded files and generated tag objects
        bagging_thread = threading.Thread(
            target=create_bag,
            args=(BAG_STORAGE_FOLDER, upload_session_token, {}, tag_objects, True)
        )
        bagging_thread.setDaemon(True)
        bagging_thread.start()
        LOGGER.info('Starting bag creation in the background')

        return HttpResponseRedirect(reverse('recordtransfer:transfersent'))


def uploadfiles(request):
    """ Upload one or more files to the server, and return a token representing the file upload
    session. If a token is passed in the request header using the Upload-Session-Token header, the
    uploaded files will be added to the corresponding session, meaning this endpoint can be hit
    multiple times for a large batch upload of files.
    """
    if not request.method == 'POST':
        return JsonResponse({'error': 'Files can only be uploaded using POST.'}, status=500)
    if not request.FILES:
        return JsonRespons({'upload_session_token': ''}, status=200)

    try:
        headers = request.headers
        if not 'Upload-Session-Token' in headers or not headers['Upload-Session-Token']:
            session = UploadSession.new_session()
            session.save()
        else:
            session = UploadSession.objects.filter(token=headers['Upload-Session-Token']).first()
            if session is None:
                session = UploadSession.new_session()
                session.save()

        for _, temp_file in request.FILES.dict().items():
            new_file = UploadedFile(name=temp_file.name, path=temp_file.path,
                old_copy_removed=False, session=session)
            new_file.save()

        return JsonResponse({'upload_session_token': session.token}, status=200)

    except Exception as exc:
        LOGGING.error('Uncaught exception in upload_file: %s' % str(exc))
        return JsonResponse({'error': f'Uncaught Exception:\n{str(exc)}'}, status=500)
