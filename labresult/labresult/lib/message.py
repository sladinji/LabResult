from labresult.model import Message, LogMessage

def log_message(user, title, channel, provider, content):
    """
    Save log for sent message in DB.
    """
    destination = user.mobile if channel == 'sms' else user.email
    user.messages.append(Message(
        title = title,
        content = content,
        channel = channel,
        destination = destination))
    user.save()
    LogMessage(user=user, title=title, channel=channel,
            provider=provider).save()


