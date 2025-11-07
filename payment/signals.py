from django.dispatch import receiver
from usuario.models import CustomUser
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

