from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from authentification.models import Utilisateur, medecinPatient
from application.models import FormulaireSante
from application.forms import FormulaireSanteForm 
import os
from django.http import HttpResponse
import numpy as np
from datetime import datetime, date, timedelta


@login_required
def accueil(request):
    prenom = request.user.username
    return render(request,"accueil.html",
                  context={"prenom": prenom})

@login_required
def comptes(request):
    regexMDP = "^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+-]).{8,}$"
    message = ""
    if request.method == "POST":
        ancienMDP = request.POST["ancienMDP"]
        nouveauMDP1 = request.POST["nouveauMDP1"]
        nouveauMDP2 = request.POST["nouveauMDP2"]
        
        verification = authenticate(username = request.user.username,
                                    password = ancienMDP)
        if verification != None:
            if nouveauMDP1 == nouveauMDP2:
                utilisateur = Utilisateur.objects.get(username = request.user.username)
                #utilisateur = Utilisateur.objects.get(id=request.user.id)
                utilisateur.set_password(request.POST.get("nouveauMDP1"))
                utilisateur.save()
                return redirect("accueil")
            else:
                message = "⚠️ Les deux mot de passe ne concordent pas ⚠️"
        else:
            message = "L'ancien mot de passe n'est pas bon. T'es qui toi ? 😡"
    return render(request,
                  "comptes.html",
                  {"regexMDP" : regexMDP, "message" : message})

@login_required
def edaia(request):
    if request.user.role == "patient":
        return redirect("https://media.tenor.com/2euSOQYdz8oAAAAj/this-was-technically-illegal-maclen-stanley.gif")
    else:
        return render(request, "edaia.html")



@login_required
def historique(request):
     # Je récupère les champs de la table formulaire santé
    champsFormulaireSante = [field.name for field in FormulaireSante._meta.get_fields()]
    # Je récupère les ids des lignes de la table formulaire santé
    idDesFormulaires = [valeur.id for valeur in FormulaireSante.objects.all()]
    # Je crée une liste qui contiendra les valeurs des lignes
    # Il y a autant d'élément que de ligne, donc que d'ids récupéré
    # FormulaireSante.objects.filter(id=id).values()[0].values()
    # Dans le code ci-dessus je récupère la ligne ayant un certain id
    # Ensuite je récupère les valeurs de la ligne .values
    # Le 1er élément qui est le dictionnaire des colonnes/valeurs
    # et enfin uniquement les valeurs
    
    #dataFormulaireSante = [FormulaireSante.objects.filter(id=id).values()[0].values() for id in idDesFormulaires]
    # On créé une liste des données du formulaires de santé général
    dataFormulaireSante = []
    # On boucle dans les lignes du formulairs > ligne 1, 2, 3...
    for id in idDesFormulaires:
        # On récupère sous forme de liste l'ensemble de la ligne ayant un id donnée
        info = list(FormulaireSante.objects.filter(id=id).values()[0].values())
        # On récupère l'username en nous basant sur la colonne de l'id dans la table du formulaire
        # On écrase l'ensemble valeur parce qu'on veut pas l'ID mais le username
        info[1] = Utilisateur.objects.filter(id=info[1])[0].username
        # On ajoute la ligne complète dans la liste dataFormulaireSante
        dataFormulaireSante.append(info)

    # Je récupère les objets patients du médecin connecté
    patientsDuMedecin = [patients for patients in medecinPatient.objects.filter(idMedecin=Utilisateur.objects.filter(username=request.user.username)[0])]
    # Je récupère les IDs des patients du médecin
    idPatientsDuMedecin = [Utilisateur.objects.filter(username=patient.idPatient)[0].id for patient in patientsDuMedecin]
    dataFormulaireSanteMedecinPatients = []

    # On boucle dans les lignes du formulairs > ligne 1, 2, 3...
    for patient in idPatientsDuMedecin:
        
        # On récupère sous forme de liste l'ensemble de la ligne ayant un id donnée
        info = list(FormulaireSante.objects.filter(patient=patient).values()[0].values())
        # On récupère l'username en nous basant sur la colonne de l'id dans la table du formulaire
        # On écrase l'ensemble valeur parce qu'on veut pas l'ID mais le username
        info[1] = Utilisateur.objects.filter(id=info[1])[0].username
        # On ajoute la ligne complète dans la liste dataFormulaireSante
        dataFormulaireSanteMedecinPatients.append(info)

    print("DDDDDDDD :", dataFormulaireSante)
    return render(request, "historique.html",
                   {"dataFormulaireSante" : dataFormulaireSante,
                   "champsFormulaireSante" : champsFormulaireSante,
                   "patientsDuMedecin" : patientsDuMedecin,
                   "dataFormulaireSanteMedecinPatients" : dataFormulaireSanteMedecinPatients})

    

@login_required
def associationMedecinPatient(request):
    # 1- Récupérer la liste des id des médecins et des patients
    # 2- Ensuite on ne garde que les patients qui ne sont pas dans la table medecinPatient
    # 3- On créé ensuite un template qui contiendra une liste déroulante
    # 4- Dans cette liste déroulante on va afficher d'un côté les médecins
    # et de l'autre les patients filtrés (voir étapge 2)
    # https://developer.mozilla.org/fr/docs/Web/HTML/Element/select
    
    medecins = [medecin for medecin in Utilisateur.objects.filter(role="medecin")]
    patients = [patient for patient in Utilisateur.objects.filter(role="patient")]
    listePatientsAssocies = [ligne.idPatient for ligne in medecinPatient.objects.all()]
    #print("listePatientsAssocies :", listePatientsAssocies)
    listePatientsNonAssocies = [patient for patient in patients if patient not in listePatientsAssocies]
    tableAssociationMedecinPatient = medecinPatient.objects.all()

    if request.method == "POST":
        medecin = request.POST["medecin"]
        patient = request.POST["patient"]
        #print("medecin", type(medecin), medecin)
        medecinPatient(idMedecin = Utilisateur.objects.filter(username=medecin)[0], 
                       idPatient = Utilisateur.objects.filter(username=patient)[0]).save()
        return redirect("associationMedecinPatient")
    return render(request, "associationMedecinPatient.html",
                  {"listePatientsNonAssocies" : listePatientsNonAssocies,
                   "medecins" : medecins,
                   "tableAssociationMedecinPatient" : tableAssociationMedecinPatient})


@login_required
def formulaireSante(request):
    message = ""
    disabled = ""
    dateDernierFormulaireDuPatient = list(FormulaireSante.objects.filter(patient=Utilisateur.objects.filter(username=request.user.username)[0]))[-1].date_remplissage
    medecinTraitant = medecinPatient.objects.filter(idPatient = Utilisateur.objects.filter(username=request.user.username)[0].id)[0].idMedecin
    periodiciteMedecin = Utilisateur.objects.filter(username=medecinTraitant)[0].periodiciteFormulaireSante
    prochainFormulaire = dateDernierFormulaireDuPatient + timedelta(days=periodiciteMedecin)
    remplirProchainFormulaire = datetime.now().date() < prochainFormulaire
    if request.method == "POST":
       #formulaire = FormulaireSanteForm(request.POST)
       #if formulaire.is_valid():
       #    sauvagarde = formulaire.save() 
       # print(request.POST)
       print(dict(request.POST).items())
    else:
        #formulaire = FormulaireSanteForm()
        if remplirProchainFormulaire:
            message = f"Le prochain formulaire devra être remplie le {prochainFormulaire}"
            disabled = "disabled"
        return render(request,
                  "formulaireSante.html",
                  {"message" : message,
                   "disabled" : disabled})


#class ApplicationWizardView(SessionWizardView):
#    form_list = [InfoGeneraleForm, EtatDeSanteForm]
#    template_name = "formulaireSante.html"
#    def done(self, form_list, **kwargs):
#            return HttpResponse('Formulaire envoyé')


       #form = form_list[0]
       #if form.cleaned_data.get('patient'):    
       #     form.save()
       
       # form = form_list
        #for form in form_list:
        #    print(form.cleaned_data.get('patient'))
        #for form in form_list:
        #    instance = form.save(commit=False)
        #return HttpResponse("Formulaire soumis !")

    

