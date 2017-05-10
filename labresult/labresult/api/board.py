from flask.ext import login
from flask import request
from mongoengine import Q

from labresult.model import Document as Doc, User, Patient
from labresult.lib.api import FilterableListResource as FLR


class Board(FLR):
    allowed_users = ["User.Administrator", "User.HealthWorker", "User.Patient"]
    doc_filter_on = {
            "User.Administrator" : 'admin',
            "User.Administrator.Biologist" : 'admin',
            "User.Administrator.AdminGeneric" : 'admin',
            "User.HealthWorker" : 'healthworkers',
            "User.Patient" : 'patient',
            "User.Group" : 'group',
            }
    model = Doc

    def _get_qry(self, args=FLR.def_args, user=None):
        """
        Return json for board api.
        """
        if not user :
            user = User.objects.get(id=login.current_user.id)
        filter_qry = self.doc_filter_on[user._cls]
        qry1 = Q()
        # filter document according to user's right :
        #  * patients can see doc where they are associated as patient
        #  * healthworkers those where they are healthworkers
        # and read acces enabled
        #  * admin those associated with their labs
        if filter_qry == 'admin' and user.labos:
            qry1 = Q(labo__in = user.labos)
        if filter_qry == 'healthworkers':
            qry1 = Q(healthworkers__match = { 'user': user.id, 'read': True })
            groups_id = [ x.user.id for x in user.groups ]
            qry1 = qry1 | Q( groups__match = {
                'user': { '$in' :groups_id },
                'read': True,
                })
        if filter_qry == 'group':
            qry1 = qry1 | Q( groups__match = {
                'user': user.id ,
                'read': True,
                })
        elif filter_qry == 'patient':
            qry1 = Q(patient__user = user, patient__read = True)

        qry2 = Q()
        filter = args['filter']
        if filter :
            qry2 = Q(patient_name__icontains=filter)
            qry2 = qry2 | Q(numdos__icontains=filter)
        patient_id = args['patient_id']

        qry3 = Q()
        if patient_id:
            patient = Patient.objects(id = patient_id).first()
            if patient :
                qry3 = Q(patient__user = patient)

        qryV = Q()
        # Do not show documents in error to LabMobile (error display not yet
        # handled by labmobile)
        if filter_qry != 'admin' or 'LabMobile' in request.user_agent.string:
            qryV = Q(current_version = True, status = Doc.OK)
        qry = Doc.objects.order_by("-date_dossier",
                "-capture_date").filter(qryV.__and__(qry1).__and__(qry2).__and__(qry3))
        return qry

