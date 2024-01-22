''' Record Transfer application models '''
import os
from pathlib import Path
import logging
import shutil
import uuid
from typing import Union

import bagit
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from caais.export import ExportVersion
from caais.models import Metadata
from recordtransfer import settings
from recordtransfer.managers import SubmissionQuerySet
from recordtransfer.storage import OverwriteStorage, UploadedFileStorage


LOGGER = logging.getLogger('recordtransfer')


class User(AbstractUser):
    ''' The main User object used to authenticate users
    '''
    gets_submission_email_updates = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)
    gets_notification_emails = models.BooleanField(default=True)

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name


class UploadSession(models.Model):
    ''' Represents a file upload session, that may or may not be split into
    multiple parallel uploads
    '''
    token = models.CharField(max_length=32)
    started_at = models.DateTimeField()

    @classmethod
    def new_session(cls):
        ''' Start a new upload session '''
        return cls(token=get_random_string(length=32), started_at=timezone.now())

    @property
    def upload_size(self):
        ''' Get total size (in bytes) of all uploaded files in this session
        '''
        return sum(f.file_upload.size for f in self.get_existing_file_set())

    def get_existing_file_set(self):
        ''' Get all files from the uploadedfile_set where the file exists
        '''
        return [f for f in self.uploadedfile_set.all() if f.exists]

    def number_of_files_uploaded(self):
        ''' Get the number of files associated with this session.

        Returns:
            (int): The number of files
        '''
        return len(self.uploadedfile_set.all())

    def remove_session_uploads(self, logger=None):
        ''' Remove uploaded files associated with this session.

        Args:
            logger: A logger object
        '''
        logger = logger or LOGGER
        existing_files = self.get_existing_file_set()
        if not existing_files:
            logger.info(msg=(
                'There are no existing uploaded files in the session {0}'\
                .format(self.token)
            ))
        else:
            logger.info(msg=(
                'Removing {0} uploaded files from the session {1}'\
                .format(len(existing_files), self.token)
            ))
            for uploaded_file in existing_files:
                uploaded_file.remove()

    def move_session_uploads(self, destination, logger=None):
        ''' Move uploaded files associated with this session to a destination directory.

        Args:
            destination (str): The destination directory
            logger: A logger object

        Returns:
            (tuple): A two tuple containing a list of the copied, and missing files
        '''
        return self._copy_session_uploads(destination, delete=True, logger=logger)

    def copy_session_uploads(self, destination, logger=None):
        ''' Copy uploaded files associated with this session to a destination directory. Files are
        not removed from their original location.

        Args:
            destination (str): The destination directory
            logger: A logger object

        Returns:
            (tuple): A two tuple containing a list of the copied, and missing files
        '''
        return self._copy_session_uploads(destination, delete=False, logger=logger)

    def _copy_session_uploads(self, destination, delete=True, logger=None):
        logger = logger or LOGGER

        destination_path = Path(destination)
        if not destination_path.exists():
            message = 'The destination path {0} does not exist!'
            logger.error(msg=message.format(destination))
            raise FileNotFoundError(message.format(destination))

        files = self.uploadedfile_set.all()

        if not files:
            logger.warning(msg=('No existing files found in the session {0}'.format(self.token)))
            return ([], [])

        verb = 'Moving' if delete else 'Copying'
        logger.info(msg=('{0} {1} temp files to {2}'.format(verb, len(files), destination)))
        copied = []
        missing = []
        for uploaded_file in files:
            source_path = uploaded_file.file_upload.path

            if not uploaded_file.exists:
                logger.error(msg=('File "{0}" was moved or deleted'.format(source_path)))
                missing.append(str(source_path))
                continue

            new_path = destination_path / uploaded_file.name
            logger.info(msg=('{0} {1} to {2}'.format(verb, source_path, new_path)))

            if delete:
                uploaded_file.move(new_path)
            else:
                uploaded_file.copy(new_path)

            copied.append(str(new_path))

        return (copied, missing)

    def __str__(self):
        return f'{self.token} ({self.started_at})'


def session_upload_location(instance, filename):
    if instance.session:
        return '{0}/{1}'.format(instance.session.token, filename)
    return 'NOSESSION/{0}'.format(filename)

class UploadedFile(models.Model):
    ''' Represents a file that a user uploaded during an upload session
    '''
    name = models.CharField(max_length=256, null=True, default='-')
    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, null=True)
    file_upload = models.FileField(null=True,
                                   storage=UploadedFileStorage,
                                   upload_to=session_upload_location)

    @property
    def exists(self):
        ''' Determine if the file this object represents exists on the file system.

        Returns:
            (bool): True if file exists, False otherwise
        '''
        return self.file_upload and self.file_upload.storage.exists(self.file_upload.name)

    def copy(self, new_path):
        ''' Copy this file to a new path.

        Args:
            new_path: The new path to copy this file to
        '''
        if self.file_upload:
            shutil.copy2(self.file_upload.path, new_path)

    def move(self, new_path):
        ''' Move this file to a new path. Marks this file as removed post-move.

        Args:
            new_path: The new path to move this file to
        '''
        if self.file_upload:
            shutil.move(self.file_upload.path, new_path)
            self.remove()

    def remove(self):
        ''' Delete the real file-system representation of this model.
        '''
        if self.file_upload:
            self.file_upload.delete(save=True)

    def __str__(self):
        if self.exists:
            return f'{self.name} | Session {self.session}'
        return f'{self.name} Removed! | Session {self.session}'


class SubmissionGroup(models.Model):
    ''' Represents a group of submissions.
    '''
    name = models.CharField(max_length=256, null=False)
    description = models.TextField(default='')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    @property
    def number_of_submissions_in_group(self):
        return len(self.submission_set.all())

    def __str__(self):
        return f'{self.name} ({self.created_by})'


class Submission(models.Model):
    ''' The object that represents a user's submission, including metadata, and
    the files they submitted.

    Attributes:
        submission_date (DateTimeField):
            The date and time the submission was made
        user (User):
            The user who submitted the metadata (and optionally, files)
        raw_form (BinaryField):
            A pickled object containing the transfer form as it was submitted
        metadata (OneToOneField):
            Foreign key to a :py:class:`~caais.models.Metadata` object. The
            metadata object is generated from the form metadata, and any
            defaults that have been set in the settings
        part_of_group (ForeignKey):
            The group that this submission is a part of
        upload_session (UploadSession):
            The upload session associated with this submission. If file uploads
            are disabled, this will always be NULL/None
        uuid (UUIDField):
            A unique ID for the submission
        bag_name (str):
            A name that is used when the Submission is to be dumped to the file
            system as a BagIt bag
    '''
    submission_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    raw_form = models.BinaryField(default=b'', null=True) # A raw capture of the form before submission
    metadata = models.OneToOneField(Metadata, on_delete=models.CASCADE, null=True, related_name='submission')
    part_of_group = models.ForeignKey(SubmissionGroup, on_delete=models.SET_NULL, blank=True, null=True)
    upload_session = models.ForeignKey(UploadSession, null=True, on_delete=models.SET_NULL)
    uuid = models.UUIDField(default=uuid.uuid4)
    bag_name = models.CharField(max_length=256, null=True)

    objects = SubmissionQuerySet.as_manager()


    def generate_bag_name(self):
        ''' Generate a name suitable for a submission bag, and set self.bag_name to that name.
        '''
        if self.bag_name:
            LOGGER.warning('generate_bag_name() was called, but self.bag_name is already set')
            return

        title = self.metadata.accession_title or 'No title'
        abbrev_title = title if len(title) <= 20 else title[0:20]

        bag_name = '{username}_{datetime}_{title}'.format(
            username=slugify(self.user.username),
            datetime=timezone.localtime(timezone.now()).strftime(r'%Y%m%d-%H%M%S'),
            title=slugify(abbrev_title)
        )

        self.bag_name = bag_name
        self.save()

    @property
    def user_folder(self):
        return os.path.join(settings.BAG_STORAGE_FOLDER, slugify(self.user.username))

    @property
    def location(self):
        """ Get the location on the file system for the BagIt bag for this submission
        """
        if not self.bag_name:
            self.make_bag_name()
        return os.path.join(self.user_folder, self.bag_name)

    @property
    def extent_statements(self):
        """ Return the first extent statement for this submission. """
        for e in self.metadata.extent_statements.get_queryset().all():
            return e.quantity_and_unit_of_measure
        return ''

    def get_admin_metadata_change_url(self):
        ''' Get the URL to change the metadata object in the admin
        '''
        view_name = 'admin:{0}_{1}_change'.format(self.metadata._meta.app_label, self.metadata._meta.model_name)
        return reverse(view_name, args=(self.metadata.pk,))

    def get_admin_metadata_change_url(self):
        ''' Get the URL to change the metadata object in the admin
        '''
        view_name = 'admin:{0}_{1}_change'.format(self.metadata._meta.app_label, self.metadata._meta.model_name)
        return reverse(view_name, args=(self.metadata.pk,))

    def get_admin_change_url(self):
        ''' Get the URL to change this object in the admin
        '''
        view_name = 'admin:{0}_{1}_change'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_report_url(self):
        ''' Get the URL to generate a report for this object in the admin
        '''
        view_name = 'admin:{0}_{1}_report'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_zip_url(self):
        """ Get the URL to generate a zipped bag for this object in the admin """
        view_name = f'admin:{self._meta.app_label}_{self._meta.model_name}_zip'
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f'Submission by {self.user} at {self.submission_date}'

    def make_bag(self, algorithms: Union[str, list] = 'sha512', file_perms: str = '644',
                 logger=None):
        """ Create a BagIt bag on the file system for this Submission. The location of the BagIt bag
        is determined by self.location. Checks the validity of the Bag post-creation to ensure that
        integrity is maintained. The data payload files come from the UploadSession associated with
        this submission.

        Args:
            algorithms (Union[str, list]): The algorithms to generate the BagIt bag with
            file_perms (str): A string-based octal "chmod" number
            logger: A logger instance (optional)
        """
        logger = logger or LOGGER

        if not algorithms:
            raise ValueError('algorithms cannot be empty')

        if isinstance(algorithms, str):
            algorithms = [a.strip() for a in algorithms.split(',')]

        for algorithm in algorithms:
            if algorithm not in bagit.CHECKSUM_ALGOS:
                raise ValueError('{0} is not a valid checksum algorithm'.format(algorithm))

        if not os.path.exists(settings.BAG_STORAGE_FOLDER) or \
                not os.path.isdir(settings.BAG_STORAGE_FOLDER):
            LOGGER.error('The BAG_STORAGE_FOLDER "%s" does not exist!', settings.BAG_STORAGE_FOLDER)
            return {
                'missing_files': [], 'bag_created': False, 'bag_valid': False,
                'time_created': None
            }

        if not os.path.exists(self.user_folder) or not os.path.isdir(self.user_folder):
            os.mkdir(self.user_folder)
            LOGGER.info('Created new user folder at "%s"', self.user_folder)

        if os.path.exists(self.location):
            LOGGER.warning('A bag already exists at "%s"', self.location)
            return {
                'missing_files': [], 'bag_created': False, 'bag_valid': False,
                'time_created': None
            }

        os.mkdir(self.location)
        LOGGER.info('Created new bag folder at "%s"', self.user_folder)

        copied, missing = self.upload_session.copy_session_uploads(self.location, logger)

        if missing:
            LOGGER.error('One or more uploaded files is missing!')
            LOGGER.info('Removing bag at "%s" due to missing files', self.location)
            self.remove_bag()
            return {
                'missing_files': missing, 'bag_created': False, 'bag_valid': False,
                'time_created': None,
            }

        logger.info('Creating BagIt bag at "%s"', self.location)
        logger.info('Using these checksum algorithm(s): %s', ', '.join(algorithms))

        bagit_info = self.metadata.create_flat_representation(version=ExportVersion.CAAIS_1_0)
        bag = bagit.make_bag(self.location, bagit_info, checksums=algorithms)

        logger.info('Setting file mode for bag payload files to %s', file_perms)
        perms = int(file_perms, 8)
        for payload_file in bag.payload_files():
            payload_file_path = os.path.join(self.location, payload_file)
            os.chmod(payload_file_path, perms)

        logger.info('Validating the bag created at "%s"', self.location)
        valid = bag.is_valid()

        if not valid:
            logger.error('Bag is INVALID!')
            logger.info('Removing bag at "%s" since it\'s invalid', self.location)
            self.remove_bag()
            return {
                'missing_files': [], 'bag_created': False, 'bag_valid': False,
                'time_created': None,
            }

        logger.info('Bag is VALID')
        current_time = timezone.now()

        return {
            'missing_files': [], 'bag_created': True, 'bag_valid': True,
            'time_created': current_time,
        }

    def remove_bag(self):
        """ Remove the BagIt bag if it exists. """
        if os.path.exists(self.location):
            os.unlink(self.location)


class Job(models.Model):
    ''' A background job executed by an admin user
    '''
    class JobStatus(models.TextChoices):
        ''' The status of the bag's review
        '''
        NOT_STARTED = 'NS', _('Not Started')
        IN_PROGRESS = 'IP', _('In Progress')
        COMPLETE = 'CP', _('Complete')
        FAILED = 'FD', _('Failed')

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    name = models.CharField(max_length=256, null=True)
    description = models.TextField(null=True)
    user_triggered = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    job_status = models.CharField(max_length=2, choices=JobStatus.choices,
                                  default=JobStatus.NOT_STARTED)
    attached_file = models.FileField(upload_to='jobs/zipped_bags', storage=OverwriteStorage,
                                     blank=True, null=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, null=True, related_name="job")

    def get_admin_change_url(self):
        ''' Get the URL to change this object in the admin
        '''
        view_name = 'admin:{0}_{1}_change'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def get_admin_download_url(self):
        ''' Get the URL to download the attached file from the admin
        '''
        view_name = 'admin:{0}_{1}_download'.format(self._meta.app_label, self._meta.model_name)
        return reverse(view_name, args=(self.pk,))

    def __str__(self):
        return f'{self.name} (Created by {self.user_triggered})'


class SavedTransfer(models.Model):
    """ A saved transfer """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_updated = models.DateTimeField(auto_now_add=True)
    current_step = models.CharField(max_length=20, null=False)
    step_data = models.BinaryField(default=b'')

    def __str__(self):
        return f"Transfer of {self.last_updated} by {self.user}"
