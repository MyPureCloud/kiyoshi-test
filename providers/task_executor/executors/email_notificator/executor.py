import os
import json
import smtplib
from smtplib import SMTPConnectError, SMTPHeloError, SMTPAuthenticationError, SMTPRecipientsRefused, SMTPSenderRefused, SMTPDataError 
import codecs
import socket
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ....common.common import FatalError
from ....common.common import GET
from ....common.common import TpaLogger 
from ....common.common import response_OK, response_BAD_REQUEST, response_INTERNAL_SERVER_ERROR
from ..helper import get_config_context
from . import settings

def _send_email(smtp_server, sender, recipients, subject, message, list_attachment_path):
    mp = MIMEMultipart()
    mp['Subject'] = subject
    mp['From'] = sender
    mp['To'] = recipients
    mp.attach(MIMEText(message, 'plain', 'utf-8'))
    
    # TODO --- handle socket.timeout exception
    try:
        s = smtplib.SMTP(smtp_server)
    except SMTPConnectError as e:
        s.quit()
        msg = "Error on connecting smtp server (SMTPConnectError). {}".format(str(e))
        with TpaLogger(**kafka) as o:
            o.error(msg)
        raise FatalError(msg)
    except smtplib.socket.timeout as e:
        msg = "Error on connecting smtp server (socket.timeout). {}".format(str(e))
        with TpaLogger(**kafka) as o:
            o.error(msg)
        raise FatalError(msg)
        
    try:
        s.sendmail(mp['From'], mp['To'], mp.as_string())
    except SMTPHeloError as e:
        msg = "Error on sending email (SMTPHeloError). {}".format(str(e))
        error(message)
        raise FatalError(message)
    except SMTPAuthenticationError as e:
        message = "Error on sending email (SMTPAuthenticationError). {}".format(str(e))
        with TpaLogger(**kafka) as o:
            o.error(msg)
        raise FatalError(msg)
    except SMTPRecipientsRefused as e:
        msg = "Error on sending email (SMTPRecipientsRefused). {}".format(str(e))
        with TpaLogger(**kafka) as o:
            o.error(msg)
        raise FatalError(msg)
    except SMTPSenderRefused as e:
        msg = "Error on sending email (SMTPSenderRefused). {}".format(str(e))
        with TpaLogger(**kafka) as o:
            o.error(msg)
        raise FatalError(msg)
    except SMTPDataError as e:
        msg = "Error on sending email (SMTPDataError). {}".format(str(e))
        with TpaLogger(**kafka) as o:
            o.error(msg)
        raise FatalError(msg)
    finally:
        s.quit()

def _send(smtp_server, sender, recipients, subject, message, attachments):
    threading.Thread(target=_send_email, args=[smtp_server, sender, recipients, subject, message, attachments]).start()

def execute(request_id, config_path, kafka, **kwargs):
    # feeds in kwargs should contain plain text for  email body text.
    if 'feeds' in kwargs:
        feeds = kwargs['feeds']
    else:
        feeds = None
    if 'attachments' in kwargs:
        with TpaLogger(**kafka) as o:
            o.INFO("NIY: attachements for email_notificator.")
        attachments = []
    else:
        attachments = []

    try:
        configurator_id = 'tpa'
        email_config = get_config_context(request_id, configurator_id, config_path, 'email_template_configuration')
    except FatalError as e:
        msg = "Failed to get config context. {}".format(str(e))
        return response_BAD_REQUEST(request_id, msg, kafka)

    try:
        smtp_server = email_config['smtp_server']
        sender = email_config['sender']
        lst_recipients = email_config['recipients']
        subject = email_config['subject']
    except KeyError as e:
        msg = "Failed to access key in email template config file. {}".format(str(e))
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    if len(lst_recipients) == 0:
        msg = "Notification not sent. There are no recipients in '{}'.".format(config_path)
        return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)
    else:
        lst = []
        for x in lst_recipients:
            lst.append(x['useremail'].encode('ascii', 'ignore'))
        recipients = ','.join(lst)

    body = ''
    if feeds:
        # the feeds has to be what something multitasks executor produced.
        # (it is not the direct response from a normal task executor)
        if type(feeds) == list:
            for x in feeds:
                s = x['output']['results']
                if type(s) == str:
                    body += s
                else:
                    with TpaLogger(**kafka) as o:
                        o.error("Unexepcted feed output results type. Expected: str, Acutal: {}.".format(type(feeds)))
        else:
            with TpaLogger(**kafka) as o:
                o.error("Unexepcted feeds type. Expected: list, Actual: {}.".format(type(feeds)))
    else:
        body = "(no body text)"

    try:
        _send(smtp_server, sender, recipients, subject, body, attachments)
    except FatalError as e:
        return response_INTERNAL_SERVER_ERROR(request_id, str(e), kafka)

    return response_OK(request_id, "Executed", body, kafka)

def get_executor(request_id, **kwargs):
    kafka = {
        'broker_server': kwargs['broker_server'],
        'broker_port': kwargs['broker_port'],
        'topic': settings.kafka['topic'],
        'key': 'default'}

    # nothing special for now
    initialized = True

    def _executor(request_id, config_path, **kwargs):
        if initialized:
            return execute(request_id, config_path, kafka, **kwargs)
        else:
            msg = "REQ[{}] {} is not operational due to initialization error.".format(request_id, settings.identity['name'])
            return response_INTERNAL_SERVER_ERROR(request_id, msg, kafka)

    return _executor

    
