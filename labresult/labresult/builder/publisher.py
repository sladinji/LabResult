from datetime import datetime

from flask.ext.babelex import gettext
from labresult.model import PublicationRule, TutorAccess


class Publisher:
    """
    Publish a document according to publication rules.
    """

    def __init__(self):
        self.refresh_rules()

    def refresh_rules(self):
        """Get publication rules from db"""
        self.patients_rules = PublicationRule.objects(
                user="patient", activated=True)
        self.hw_rules = PublicationRule.objects(
                user__ne="patient", activated=True)

    def _apply_patient_rules(self, doc):
        access = doc.patient
        if doc.patient.user.tutor:
            doc.tutor = TutorAccess(user = doc.patient.user.tutor)
            access = doc.tutor
        access.read = True
        access.pub_date = datetime.now()
        rules = [r for r in self.patients_rules]
        fails = [ r for r in rules if not r.apply(doc) ]
        self._update_access(access, rules, fails)

    def _update_access(self, access, rules, fails):
        """
        :param access: HealthWorkerAccess
        :param rules: rules applied
        :param fails: rules who failed
        """
        access.read = True
        role = access.role if hasattr(access, "role") else "patient"
        if not rules :
            access.comment = gettext("No rules for %s").format(gettext(role))
            access.read = False
            return
        for rule in fails:
                access.read = False
                if not access.comment :
                    access.comment = rule.msg_error
                else :
                    access.comment += '\n' + rule.msg_error

    def _apply_hw_rules(self, doc):
        for hw in doc.healthworkers :
            hw.pub_date = datetime.now()
            rules = [r for r in self.hw_rules if r.user == hw.role]
            fails = [ r for r in rules if not r.apply(doc) ]
            self._update_access(hw, rules, fails)
            if not hw.read :
                continue
            shares = [g.user for g in hw.user.groups if g.share]
            groupsaccess = [ga for ga in doc.groups if ga.user in shares]
            for group in groupsaccess:
                group.read = True


    def publish_document(self, doc):
        self._apply_patient_rules(doc)
        self._apply_hw_rules(doc)
