import glob
import os
import random
import sys

import labresult
from labresult import create_app
from labresult.model import *


def add_admin():
    """
    Script to add admin user
    """
    if len(sys.argv) < 4:
        print("Usage :add_admin conf(dev, prod...) login pass")
    labresult.app, labresult.celery = labresult.create_app(sys.argv[1])
    admin = AdminGeneric(login=sys.argv[2], pass2hash=sys.argv[3],
            account_activated = True)
    admin.save()

def set_demo_options(nb_result=5):
    """
    publication rules
    underlay
    biologist and secretary roles
    default users
    """
    labresult.app, labresult.celery = create_app(sys.argv[1])
    from labresult.lib.conf import do_post_config
    do_post_config(labresult.app)
    PublicationRule.drop_collection()
    prule = PublicationRule(
            comment = "Documents diffusés aux patients",
            msg_error = "Type de document non accessible aux patients",
            user = "patient",
            rule = "doc.doc_type in ['CR_PATIENT']",
            activated = True)
    prule.save()
    drule = PublicationRule(
            comment = "Documents diffusés aux professionnels médecins",
            msg_error = "Type de document non accessible aux médecins",
            user = "doctor",
            rule = "doc.doc_type in ['CR_DOCTOR']",
            activated = True)
    drule.save()
    folder = os.path.join(os.path.dirname(__file__), 'underlay')
    ufile = os.path.join(folder,"underlay.pdf")
    Underlay.drop_collection()
    underlay = Underlay(
            name = "Entête LabResult",
            doc_types = ['CR_PATIENT', 'CR_DOCTOR'],
            all_pages = False,
            comment = "Entête LabResult",
            )
    underlay.recto.put( open(ufile,'rb'), content_type = "application/pdf",
            filename = "entête-labresult.pdf")
    underlay.save()
    Printer.drop_collection()
    printer = Printer(name="Print LabResult",
            is_default = True,
            cups_host = "print_server",
            cups_port = 631,
            activated = True,
            )
    printer.save()
    Labo.drop_collection()
    labo = Labo(external_id="1",
            name="LabResult Labo",
            )
    labo.underlays.append(underlay)
    labo.printers.append(printer)
    labo.save()
    AdminRole.drop_collection()
    biorole = AdminRole(
            name = "biologiste",
            acl = [
                Right(
                    view = View.objects.filter(
                        name = 'DocumentView',
                        ).first(),
                    create = False,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'PatientView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'AdminView',
                        ).first(),
                    create = True,
                    read = True,
                    update = False,
                    delete = False,),
                Right(
                    view = View.objects.filter(
                        name = 'GroupView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'HealthWorkerView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'LaboView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'UnderlayView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'PrinterView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'PublicationView',
                        ).first(),
                    create = True,
                    read = True,
                    update = True,
                    delete = True,),
                Right(
                    view = View.objects.filter(
                        name = 'UserLogView',
                        ).first(),
                    create = False,
                    read = True,
                    update = False,
                    delete = False,),
                ]
                )
    biorole.save()
    secrole = AdminRole(
            name = "secrétaire",
            acl = [
                Right(
                    view = View.objects.filter(
                        name = 'PatientView',
                        ).first(),
                    create = False,
                    read = True,
                    update = False,
                    delete = False,),
                Right(
                    view = View.objects.filter(
                        name = 'HealthWorkerView',
                        ).first(),
                    create = False,
                    read = True,
                    update = False,
                    delete = False,),
                Right(
                    view = View.objects.filter(
                        name = 'GroupView',
                        ).first(),
                    create = False,
                    read = True,
                    update = False,
                    delete = False,),
                Right(
                    view = View.objects.filter(
                        name = 'AdminView',
                        ).first(),
                    create = False,
                    read = True,
                    update = False,
                    delete = False,),
                Right(
                    view = View.objects.filter(
                        name = 'UserLogView',
                        ).first(),
                    create = False,
                    read = True,
                    update = False,
                    delete = False,),
                ]
            )
    secrole.save()
    admin = AdminGeneric(login="admin", pass2hash="labdemo",
            account_activated=True, name="Mr Admin Démo" )
    admin.save()
    biolo = Biologist(login="biologiste", pass2hash="labdemo",
            role=biorole, account_activated=True, name="Mr Biologiste Démo")
    biolo.save()
    secretary = AdminGeneric(login="secretaire", pass2hash="labdemo",
            role=secrole, account_activated=True, name="Mr Secrétaire Démo")
    secretary.save()
    _gen_result(nb_result)
    pat = Patient.objects[0]
    pat.login = "patient"
    pat.set_pass("labdemo")
    pat.account_activated = True
    pat.save()
    doc = HealthWorker.objects[0]
    doc.login = "docteur"
    doc.set_pass("labdemo")
    doc.account_activated = True
    doc.save()

def gen_result():
    if len(sys.argv) < 3:
        print("Usage : gen_result conf(dev, prod...) nb_results")
    labresult.app, labresult.celery = create_app(sys.argv[1])
    nb_results = int(sys.argv[2])
    _gen_result(nb_results)

def _gen_result(nb_results):
    from labresult.builder.tasks import integrate
    from labresult.converter import get_pdf, get_img

    patients = [
    {
        'npat': '1',
        'prn' : 'Jean',
        'pnom': 'Valjean',
        'nmob' : '07.82.42.32.12',
        'age' : '23/08/1978',
        'ddn' : '13/05/1980',
        'nSS' : '123456789098765',
        'pfx' : 'Mr',
        'ad1' : '7 rue Eric Satie',
        'ad2' : r'25000 Besan\on',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '2',
        'prn' : 'Leon',
        'pnom': 'Jurado',
        'nmob' : '07.82.42.32.12',
        'age' : '23/08/1978',
        'nSS' : '198678435654324',
        'pfx' : 'Mr',
        'ad1' : '18 rue du muguet',
        'ad2' : '54000 Nancy',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '3',
        'prn' : 'Julie',
        'pnom': 'Gatero',
        'nmob' : '07.82.42.32.12',
        'age' : '04/06/1950',
        'pfx' : 'Mme',
        'nSS' : '298067417654209',
        'ad1' : '7 chemin des saulniers',
        'ad2' : '94140 AlfortVille',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '4',
        'prn' : 'Syvie',
        'pnom': 'Durant',
        'nmob' : '07.82.42.32.12',
        'age' : '14/09/1998',
        'nSS' : '276098321876543',
        'pfx' : 'Mlle',
        'ad1' : '5 bis avenue du parc',
        'ad2' : r'25000 Besan\on',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '5',
        'prn' : 'Evelyne',
        'pnom': 'Regolini',
        'nmob' : '07.82.42.32.12',
        'age' : '20/03/1949',
        'nSS' : '287987092398541',
        'pfx' : 'Mme',
        'ad1' : '9 rue des prairies',
        'ad2' : '21000 Dijon',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '6',
        'prn' : 'Jean-Pierre',
        'pnom': 'Quiro',
        'nmob' : '07.82.42.32.12',
        'age' : '06/07/1987',
        'nSS' : '167980915432876',
        'pfx' : 'Mr',
        'ad1' : '1 place de la mairie',
        'ad2' : '29019 Brest',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '7',
        'prn' : 'Fabien',
        'pnom': 'Chapuzot',
        'nmob' : '07.82.42.32.12',
        'age' : '24/11/1990',
        'nSS' : '187095432876432',
        'pfx' : 'Mr',
        'ad1' : 'Impasse de la chanelle',
        'ad2' : '90000 Belfort',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '8',
        'prn' : 'Marie',
        'pnom': 'Parisot',
        'nmob' : '07.82.42.32.12',
        'age' : '30/09/1981',
        'nSS' : '278675409653254',
        'pfx' : 'Mme',
        'ad1' : '3 Rue du chêne benit',
        'ad2' : '25870 Geneuille',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '9',
        'prn' : 'Rose-Marie',
        'pnom': 'Jacques',
        'nmob' : '07.82.42.32.12',
        'age' : '01/08/2001',
        'nSS' : '287093198532987',
        'pfx' : 'Mlle',
        'ad1' : '6 chenim des tulipes',
        'ad2' : '70000 Vesoul',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '10',
        'prn' : 'Adrien',
        'pnom': 'Sinicci',
        'nmob' : '07.82.42.32.12',
        'age' : '09/01/1987',
        'nSS' : '198543198765432',
        'pfx' : 'Mr',
        'ad1' : '32 rue de la république',
        'ad2' : '25640 Roulans',
        'tel' : '07.82.42.32.12',
    },
    {
        'npat': '11',
        'prn' : 'Jeanne',
        'pnom': 'Dupont',
        'nmob' : '07.82.42.32.12',
        'age' : '16/12/1980',
        'nSS' : '287098365432198',
        'pfx' : 'Mlle',
        'ad1' : '6 rue du abel monnot',
        'ad2' : '25115 Pouilley les Vignes',
        'tel' : '07.82.42.32.12',
    },


    ]



    medecins = [
    {
        'nommed' : 'Dr ROBERT Louison',
        'cmed' : 'med1',
        'adm1' : '7 rue Antoine B{champ',
        'adm2' : '69001 Lyon',

    },
    {
        'nommed' : 'Dr LONORU Fabienne',
        'cmed' : 'med2',
        'adm1' : '8 rue F{lix Dujardin',
        'adm2' : '13003 Marseille'

    },
    {
        'nommed' : 'Dr MARTIN Suzanne',
        'cmed' : 'med3',
        'adm1' : '8 rue Jean Dausset',
        'adm2' : '31000 Toulouse',

    },
    {
        'nommed' : 'Dr PAUL Jacques',
        'cmed' : 'med4',
        'adm1' : '15 rue Marie Curie',
        'adm2' : '94140 AlfortVille',

    },
    {
        'nommed' : 'Dr VERNIER Marie',
        'cmed' : 'med5',
        'adm1' : "20 rue Saturnin Arloing",
        'adm2' : '69002 Lyon',

    },
    ]

    # envoi générations à partir des templates
    folder = os.path.join(os.path.dirname(__file__), 'pcltemplates')
    l = glob.glob(os.path.join(folder, '*'))
    l.sort()
    dossiers = {}
    for fn in l[::2] :
        numdos = fn[len(folder):len(folder)+10]
        dossiers.update({
                numdos :dict(
                    pat=open("%s/%s" % (folder, numdos + "-P1##.pcl"), "r").read(),
                    doc=open("%s/%s" % (folder, numdos + "-M1A##.pcl"),"r").read(),
                    )
                }
            )
    count = 0
    while count < nb_results :
        for numdos, datas in dossiers.items():
            if count == nb_results :
                break
            mapping = {}
            mapping.update(random.choice(patients))
            mapping.update(random.choice(medecins))
            now = datetime.datetime.now()
            newnumdos = now.strftime("%y%m%d") + "%03d" % random.randint(1, 250)
            newdatedos = now.strftime("%d/%m/%y")
            mapping.update(datedos=newdatedos)
            mapping.update(numdos=newnumdos)
            mapping.update(city='Besan\\on')
            mapping.update(adm3="")
            mapping.update(ad3="")
            mapping.update(cprl="")
            mapping.update(nprl="")
            mapping.update(tdu=random.randint(0,1))
            mapping.update(ddn=mapping['age'])
            mapping.update(Type="P1##")
            template = datas['pat'].replace('% ', '%% ')
            try:
                count +=1
                data = template % mapping
                docid = integrate(data=data.encode('cp437'))
                doc = Document.objects.get(id=docid)
                get_pdf(doc)
                get_img(doc, 1, True, 'png')
                #try to associate a biologiste to document
                biolo = Biologist.objects.first()
                if biolo :
                    doc.biologist = biolo
                    doc.save()
                mapping.update(Type="M1A##")
                data = datas['doc'] % mapping
                docid = integrate(data=data.encode('cp437'))
                doc = Document.objects.get(id=docid)
                get_pdf(doc)
                get_img(doc, 1, True, 'png')
                #try to associate a biologiste to document
                biolo = Biologist.objects.first()
                if biolo :
                    doc.biologist = biolo
                    doc.save()
            except Exception as e:
                print(e)
