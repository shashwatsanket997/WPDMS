from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from django.views.generic import CreateView,UpdateView,DeleteView
from .models import WarrentyYear,WaterPlant,WaterPlantLoc,Consumables,Cost,repair_parts,User
from .forms import WaterPlantLocForm,InchargeForm
from django.urls import reverse_lazy
from datetime import datetime as dt
import datetime as dtt
import xlwt
import xlrd
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from .decorators import superuser
# Create your views here.


def index(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    else:
        if(request.user.is_superuser):
            wp=WaterPlant.objects.all()
            total=len(wp)
            return render(request,'index.html',{'total':total})
        else:
            return render(request,'dashboard_incharge.html')

def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request,user)
                if(user.is_superuser):
                    return render(request, 'index.html')
                else:
                    return render(request,'dashboard_incharge.html')
            else:
                return render(request, 'login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'login.html', {'error_message': 'Invalid login'})
    return render(request, 'login.html')


def logout_user(request):
    logout(request)
    return render(request, 'login.html')


def get_set_of_locs():
    district=WaterPlantLoc.objects.all().values_list('district').distinct()
    district=[i[0] for i in district]
    mandal=WaterPlantLoc.objects.all().values_list('mandal').distinct()
    mandal=[i[0] for i in mandal]
    gram_panchayat=WaterPlantLoc.objects.all().values_list('gram_panchayat').distinct()
    gram_panchayat=[i[0] for i in gram_panchayat]
    village=WaterPlantLoc.objects.all().values_list('village').distinct()
    village=[i[0] for i in village]
    constency=WaterPlantLoc.objects.all().values_list('constency').distinct()
    constency=[i[0] for i in constency]
    context={
        'district':district,
        'mandal':mandal,
        'gram_panchayat':gram_panchayat,
        'village':village,
        'constency':constency,
        'users':User.objects.filter(is_superuser=False),
    }
    return context

def get_set_of_locs_inWP(user):
    if(user.is_superuser):
        locs=WaterPlant.objects.all().values_list('loc').distinct()
    else:
        locs=WaterPlant.objects.filter(incharge=user).values_list('loc').distinct()
    district=set([WaterPlantLoc.objects.get(pk=i[0]).district for i in locs])
    mandal=set([WaterPlantLoc.objects.get(pk=i[0]).mandal for i in locs])
    gram_panchayat=set([WaterPlantLoc.objects.get(pk=i[0]).gram_panchayat for i in locs])
    village=set([WaterPlantLoc.objects.get(pk=i[0]).village for i in locs])
    constency=set([WaterPlantLoc.objects.get(pk=i[0]).constency for i in locs])
    context={
        'district':district,
        'mandal':mandal,
        'gram_panchayat':gram_panchayat,
        'village':village,
        'constency':constency,
    }
    return context


@login_required
@superuser
def CreateWaterPlant(request):
    context=get_set_of_locs()
    if "GET" == request.method:
        return render(request,'CreateWaterPlant.html',context)
    else:
        district=request.POST.get('district').strip().title()
        mandal=request.POST.get('mandal').strip().title()
        gram_panchayat=request.POST.get('gram_panchayat').strip().title()
        village=request.POST.get('village').strip().title()
        constency=request.POST.get('constency').strip().title()
        populations=request.POST.get('populations').strip().title()
        capacity=request.POST.get('capacity').strip().title()
        date=request.POST.get('date').strip()
        plant_type=request.POST.get('plant_type').strip()
        incharge=request.POST.get('id_incharge').strip()
        incharge=User.objects.get(pk=int(incharge))
        if(plant_type=="None"):
            context['error_message']=['Please select plant type']
        try:
            date=dt.strptime(date,"%Y-%m-%d")#datetype format
        except:
            context['error_message']=['Please check the date']
            return render(request,'CreateWaterPlant.html',context)
        contact_person=request.POST.get('contact_person').strip().title()
        contact_number=request.POST.get('contact_number').strip().title()
        operator_name=request.POST.get('operator_name').strip().title()
        operator_phone_number=request.POST.get('operator_phone_number').strip().title()
        #processing location
        try:
            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
        except WaterPlantLoc.DoesNotExist:
            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
            loc.save()
        #caluculating for is_amc
        todays_date=dt.now()
        difference=todays_date-date
        warrenty=int(WarrentyYear.objects.all()[0].year)
        if(difference.days>warrenty*365.25):
            is_amc=True
        else:
            is_amc=False

        #populations Exception
        error_message=[]
        success_message=[]
        if(int(populations)<=0):
            error_message.append("Population should be greater than 0")
        if(int(float(capacity))<=0):
            error_message.append("Capacity should be greater than 0")
        if(len(contact_number)<10 or not contact_number.isdigit()):
            error_message.append("Contact Number should be of 10 digits")
        if(len(operator_phone_number)<10 or not operator_phone_number.isdigit()):
            error_message.append("operator_phone_number Number should be of 10 digits")
        #saving the water plant 
        context=get_set_of_locs()
        if(len(error_message)>0):
            context['error_message']=error_message
            return render(request,'CreateWaterPlant.html',context)
        else:
            Wp=WaterPlant(loc=loc,populations=populations,capacity=capacity,date=date,contact_person=contact_person,contact_number=contact_number,operator_name=operator_name,operator_phone_number=operator_phone_number,incharge=incharge,plant_type=plant_type,is_amc=is_amc)
            Wp.save()
            if(not is_amc):
                context['success_message']=["Water Plant successfully created and fall under new plant "+"Plant name:-"+village +' check the database']
            else:
                context['success_message']=["Water Plant successfully created and fall under AMC plant "+"Plant name:-"+village +' check the database'] 
            return render(request,'CreateWaterPlant.html',context)


@login_required
@superuser
def UpdateWaterPlant_form(request,pk):
    context=get_set_of_locs()
    if "GET" == request.method:
        return render(request,'CreateWaterPlant.html',context)
    else:
        district=request.POST.get('district').strip().title()
        mandal=request.POST.get('mandal').strip().title()
        gram_panchayat=request.POST.get('gram_panchayat').strip().title()
        village=request.POST.get('village').strip().title()
        constency=request.POST.get('constency').strip().title()
        populations=request.POST.get('populations').strip().title()
        capacity=request.POST.get('capacity').strip().title()
        date=request.POST.get('date').strip()
        plant_type=request.POST.get('plant_type').strip()
        incharge=request.POST.get('id_incharge').strip()
        incharge=User.objects.get(pk=int(incharge))
        if(plant_type=="None"):
            context['error_message']=['Please select plant type']
        try:
            date=dt.strptime(date,"%Y-%m-%d")#datetype format
        except:
            context['error_message']=['Please check the date']
            return render(request,'CreateWaterPlant.html',context)
        contact_person=request.POST.get('contact_person').strip().title()
        contact_number=request.POST.get('contact_number').strip().title()
        operator_name=request.POST.get('operator_name').strip().title()
        operator_phone_number=request.POST.get('operator_phone_number').strip().title()
        #processing location
        try:
            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
        except WaterPlantLoc.DoesNotExist:
            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
            loc.save()
        #caluculating for is_amc
        todays_date=dt.now()
        difference=todays_date-date
        warrenty=int(WarrentyYear.objects.all()[0].year)
        if(difference.days>warrenty*365.25):
            is_amc=True
        else:
            is_amc=False

        #populations Exception
        error_message=[]
        success_message=[]
        if(int(populations)<=0):
            error_message.append("Population should be greater than 0")
        if(int(float(capacity))<=0):
            error_message.append("Capacity should be greater than 0")
        if(len(contact_number)<10 or not contact_number.isdigit()):
            error_message.append("Contact Number should be of 10 digits")
        if(len(operator_phone_number)<10 or not operator_phone_number.isdigit()):
            error_message.append("operator_phone_number Number should be of 10 digits")
        #saving the water plant 
        context=get_set_of_locs()
        if(len(error_message)>0):
            context['error_message']=error_message
            return render(request,'CreateWaterPlant.html',context)
        else:
            Wp=WaterPlant.objects.filter(pk=pk).update(loc=loc,populations=populations,capacity=capacity,date=date,contact_person=contact_person,contact_number=contact_number,operator_name=operator_name,operator_phone_number=operator_phone_number,incharge=incharge,plant_type=plant_type,is_amc=is_amc)
            if(not is_amc):
                context['success_message']=["Water Plant successfully created and fall under new plant "+"Plant name:-"+village +' check the database']
            else:
                context['success_message']=["Water Plant successfully created and fall under AMC plant "+"Plant name:-"+village +' check the database'] 
            return render(request,'CreateWaterPlant.html',context)

@login_required
@superuser          
def water_plant_import(request):
    if "GET"==request.method:
        return render(request,'WaterPlantImport.html')
    else:
        csv_file = request.FILES["csv_file"]
        if not (csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.csv') or csv_file.name.endswith('.xls')):
            context={"error_message1":["File is not .csv/.xlsx/.xls type"]}
            return render(request, "WaterPlantImport.html", context)
        if csv_file.multiple_chunks():
            context={"error_message1":["Uploaded file is too big."]}
            return render(request, "WaterPlantImport.html", context)
        if (csv_file.name.endswith('.csv')):
            file_data = csv_file.read().decode("utf-8")
            lines = file_data.split("\n")[1:]
            updated=[]
            go_ahead=True
            for line in lines:
                inf=''
                fields = line.split(",")
                if(len(fields)==13):
                    try:
                        district=fields[0].rstrip('\r').title()
                        mandal=fields[1].rstrip('\r').title()
                        gram_panchayat=fields[2].rstrip('\r').title()
                        village=fields[3].rstrip('\r').title()
                        constency=fields[4].rstrip('\r').title()
                        populations=fields[5].rstrip('\r').title()
                        capacity=fields[6].rstrip('\r').title()
                        date=fields[7].rstrip('\r').title()
                        contact_person=fields[8].rstrip('\r').title()
                        contact_number=fields[9].rstrip('\r').title()
                        operator_name=fields[10].rstrip('\r').title()
                        operator_phone_number=fields[11].rstrip('\r').title()
                        plant_type=fields[12].rstrip('\r').upper()
                        try:
                            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            inf="Using the location:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                        except:
                            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            loc.save()
                            inf="location Created for:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                        updated.append(inf)
                        #Handiling dates
                        try:
                            date=dt.strptime(date,"%d/%m/%Y")#datetype format
                        except:
                            updated.append('Improper date format at line:-'+str(lines.index(line)+1))
                            go_ahead=False
                        #caluculating for is_amc
                        todays_date=dt.now()
                        difference=todays_date-date
                        warrenty=int(WarrentyYear.objects.all()[0].year)
                        if(difference.days>warrenty*365.25):
                            is_amc=True
                        else:
                            is_amc=False
                        if(int(populations)<=0):
                            updated.append("Population should be greater than 0")+str(lines.index(line)+1)
                            go_ahead=False
                        if(int(float(capacity))<=0):
                            updated.append("Capacity should be greater than 0"+str(lines.index(line)+1))
                            go_ahead=False
                        if(len(contact_number)<10 or not contact_number.isdigit()):
                            updated.append("Contact Number should be of 10 digits"+str(lines.index(line)+1))
                            go_ahead=False
                        if(len(operator_phone_number)<10 or not operator_phone_number.isdigit()):
                            updated.append("operator_phone_number Number should be of 10 digits"+str(lines.index(line)+1))
                            go_ahead=False
                        if(go_ahead):
                            Wp=WaterPlant(loc=loc,populations=populations,capacity=capacity,date=date,contact_person=contact_person,contact_number=contact_number,operator_name=operator_name,operator_phone_number=operator_phone_number,plant_type=plant_type,is_amc=is_amc)
                            Wp.save()
                            updated.append("Data Saved for Water Plant at line number:-"+str(lines.index(line)+1))
                    except:
                        updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
                else:
                    updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
            updated.append("-----------------Processing Completed-----------------")
            context={
            'process_status': updated,
            }    
            return render(request, "WaterPlantImport.html", context)
        elif(csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.xls')):
            book = xlrd.open_workbook(file_contents=csv_file.read())
            sheet = book.sheet_by_index(0)
            data=[]
            p=[]
            for i in range(1,sheet.nrows):
                data.append(sheet.row_values(i))
            lines=data
            updated=[]
            for line in lines:
                go_ahead=True
                inf=''
                fields = line
                if(len(fields)==13):
                    try:
                        district=fields[0].rstrip('\r').title()
                        mandal=fields[1].rstrip('\r').title()
                        gram_panchayat=fields[2].rstrip('\r').title()
                        village=fields[3].rstrip('\r').title()
                        constency=fields[4].rstrip('\r').title()
                        populations=str(fields[5]).rstrip('\r').title()
                        capacity=str(fields[6]).rstrip('\r').title()
                        wrongValue=fields[7]
                        workbook_datemode = book.datemode
                        date=dtt.datetime(*xlrd.xldate_as_tuple(wrongValue,workbook_datemode))
                        contact_person=fields[8].rstrip('\r').title()
                        contact_number=str(int(fields[9])).rstrip('\r').title()
                        operator_name=fields[10].rstrip('\r').title()
                        operator_phone_number=str(int(fields[11])).rstrip('\r').title()
                        plant_type=fields[12].rstrip('\r').title()
                        try:
                            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            inf="Using the location:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                        except:
                            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            loc.save()
                            inf="location Created for:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                        updated.append(inf)
                        #Handiling dates
                        #caluculating for is_amc
                        todays_date=dt.now()
                        difference=todays_date-date
                        warrenty=int(WarrentyYear.objects.all()[0].year)
                        if(difference.days>warrenty*365.25):
                            is_amc=True
                        else:
                            is_amc=False
                        if(int(float(populations))<=0):
                            updated.append("Population should be greater than 0")+str(lines.index(line)+1)
                            go_ahead=False
                        
                        if(int(float(capacity))<=0):
                            updated.append("Capacity should be greater than 0"+str(lines.index(line)+1))
                            go_ahead=False
                       
                        if(not contact_number.isdigit()):
                            updated.append("Contact Number should be of 10 digits"+str(lines.index(line)+1))
                            go_ahead=False
                        
                        if(not operator_phone_number.isdigit()):
                            updated.append("operator_phone_number Number should be of 10 digits"+str(lines.index(line)+1))
                            go_ahead=False
                        if(go_ahead):
                            try:
                                wp=WaterPlant.objects.get(loc=loc,populations=populations,capacity=capacity,date=date,contact_person=contact_person,contact_number=contact_number,operator_name=operator_name,operator_phone_number=operator_phone_number,plant_type=plant_type,is_amc=is_amc)
                                updated.append("Date already exists for the line:-"+str(lines.index(line)+1))
                            except:
                                Wp=WaterPlant(loc=loc,populations=populations,capacity=capacity,date=date,contact_person=contact_person,contact_number=contact_number,operator_name=operator_name,operator_phone_number=operator_phone_number,incharge=incharge,plant_type=plant_type,incharge_phone_number=incharge_phn_number,is_amc=is_amc)
                                Wp.save()
                                updated.append("Data Saved for Water Plant at line number:-"+str(lines.index(line)+1))
                        else:
                            updated.append("Rectify the error at line number:-"+str(lines.index(line)+1))
                    except:
                        updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
                else:
                    updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
            updated.append("-----------------Processing Completed-----------------")
            context={
            'process_status': updated,
            }    
            return render(request, "WaterPlantImport.html", context)


@login_required
@superuser
def sample_download(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="WaterPlant.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('WPDMS')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    date_format = xlwt.XFStyle()
    date_format.num_format_str = 'dd/mm/yyyy'
    columns = ['District','Mandal','Gram Panchayat','Village','Constency','Population','Capacity','Date','Contact Person','Pnone Number','Operator Name','Pnone Number','Plant Type']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    wb.save(response)
    return response


@login_required
@superuser
def view_new_water_plants(request):
    NewWp=WaterPlant.objects.filter(is_amc=False)
    context=get_set_of_locs()
    context['data']=NewWp
    return render(request,'NewWaterPlanDB.html',context)

@login_required
@superuser
def view_amc_water_plants(request):
    NewWp=WaterPlant.objects.filter(is_amc=True)
    context=get_set_of_locs()
    context['data']=NewWp
    return render(request,'AMCWaterPlantDB.html',context)
    
@login_required
@superuser 
def WaterPlantUpdate(request,pk):
    data=WaterPlant.objects.get(pk=pk)
    context=get_set_of_locs()
    context['data']=data
    return render(request,'WPlandingpage.html',context)

@login_required
@superuser
def WaterPlantDelete(request,pk):
    data=WaterPlant.objects.get(pk=pk)
    is_amc=data.is_amc
    data.delete()
    data=WaterPlant.objects.filter(is_amc=is_amc)
    context={
        'success_message':'Successfully Deleted',
        'data':data,
    }
    if(is_amc):
        return render(request,'NewWaterPlanDB.html',context)
    else:
        return render(request,'AMCWaterPlantDB.html',context)



@login_required
@superuser
def CreateWaterPlantLoc(request):
    form=WaterPlantLocForm(request.POST or None)
    if form.is_valid():
        district=form.cleaned_data['district'].title()
        mandal=form.cleaned_data['mandal'].title()
        gram_panchayat=form.cleaned_data['gram_panchayat'].title()
        village=form.cleaned_data['village'].title()
        constency=form.cleaned_data['constency'].title()
        try:
            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
            context={
            "error_message":'Data already exists',
            }
        except:
            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
            loc.save()
            context={
            "success_message":'Data Saved',
            }
        return render(request,'CreateWaterPlantLoc.html',context=context)
    else:
        return render(request,'CreateWaterPlantLoc.html')

@login_required
@superuser
def CreateWaterPlantLocViaImport(request):
    if "GET" == request.method:
        return render(request, "CreateWaterPlantLoc.html")
    else:
        csv_file = request.FILES["csv_file"]
        if not (csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.csv') or csv_file.name.endswith('.xls')):
            context={"error_message1":["File is not .csv/.xlsx/.xls type"]}
            return render(request, "CreateWaterPlantLoc.html", context)
        if csv_file.multiple_chunks():
            context={"error_message1":["Uploaded file is too big."]}
            return render(request, "CreateWaterPlantLoc.html", context)
        if (csv_file.name.endswith('.csv')):
            file_data = csv_file.read().decode("utf-8")
            lines = file_data.split("\n")[1:]
            updated=[]
            for line in lines:
                inf=''
                fields = line.split(",")
                if('' in fields):
                    fields.remove('')
                if(len(fields)==5):
                    try:
                        district=fields[0].rstrip('\r').title()
                        mandal=fields[1].rstrip('\r').title()
                        gram_panchayat=fields[2].rstrip('\r').title()
                        village=fields[3].rstrip('\r').title()
                        constency=fields[4].rstrip('\r').title()
                        try:
                            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            inf="Data Already Exist at:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                            updated.append(inf)
                        except:
                            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            loc.save()
                            inf="Data Saved for:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                            updated.append(inf)
                    except:
                        updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
                else:
                    updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
            updated.append("-----------------Processing Completed-----------------")
            context={
            'process_status': updated,
            }    
            return render(request, "CreateWaterPlantLoc.html", context)
        elif(csv_file.name.endswith('.xlsx') or csv_file.name.endswith('.xls')):
            book = xlrd.open_workbook(file_contents=csv_file.read())
            sheet = book.sheet_by_index(0)
            data=[]
            p=[]
            for i in range(1,sheet.nrows):
                data.append(sheet.row_values(i))
            lines=data
            updated=[]
            for line in lines:
                inf=''
                fields = line
                if('' in fields):
                    fields.remove('')
                if(len(fields)==5):
                    try:
                        district=fields[0].rstrip('\r').title()
                        mandal=fields[1].rstrip('\r').title()
                        gram_panchayat=fields[2].rstrip('\r').title()
                        village=fields[3].rstrip('\r').title()
                        constency=fields[4].rstrip('\r').title()
                        try:
                            loc=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            inf="Data Already Exist at:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                            updated.append(inf)
                        except:
                            loc=WaterPlantLoc(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
                            loc.save()
                            inf="Data Saved for:-" +str(lines.index(line)+1)+" "+district+' | '+mandal+' | ' +gram_panchayat+' | '+village+' | '+constency
                            updated.append(inf)
                    except:
                        updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
                else:
                    updated.append("Got unexpected garbage value or unprocessed value at line number:->"+str(lines.index(line)+1))        
            updated.append("-----------------Processing Completed-----------------")
            context={
            'process_status': updated,
            }    
            return render(request, "CreateWaterPlantLoc.html", context)

    



@login_required
@superuser
def WaterPlantLocUpdate(request,pk):
    data=WaterPlantLoc.objects.get(pk=pk)
    context={
        'data':data,
    }
    return render(request,'WaterPlantLocUpdate.html',context)

@login_required
@superuser
def WaterPlantLocDelete(request,pk):
    data=WaterPlantLoc.objects.get(pk=pk)
    data.delete()
    data=WaterPlantLoc.objects.all()
    context={
        'success_message':'Successfully Deleted',
        'data':data,
    }
    return render(request,'WaterPlantLocDB.html',context)

@login_required
@superuser
def WaterPlantLocDB(request):
    data=WaterPlantLoc.objects.all()
    context={
        'data':data,
    }
    return render(request,'WaterPlantLocDB.html',context=context)

@login_required
@superuser
def SetWarrentyDate(request):
    return render(request,'WarrentyDate.html')


@login_required
def load_district(request):
    loc=WaterPlantLoc.objects.all().values_list('district').distinct()
    return render(request,"load_district.html",{'district':district})

@login_required
def load_mandal(request):
    district=request.GET.get('district')
    mandals=WaterPlantLoc.objects.filter(district=district).values_list('mandal').distinct()
    mandals=[i[0] for i in mandals]
    return render(request,"load_mandal.html",{'mandal':mandals})

@login_required
def load_gram_panchayat(request):
    mandal=request.GET.get('mandal')
    gram_panchayat=WaterPlantLoc.objects.filter(mandal=mandal).values_list('gram_panchayat').distinct()
    gram_panchayat=[i[0] for i in gram_panchayat]
    return render(request,"load_gram_panchayat.html",{'gram_panchayat':gram_panchayat})

@login_required
def load_village(request):
    gram_panchayat=request.GET.get('gram_panchayat')
    village=WaterPlantLoc.objects.filter(gram_panchayat=gram_panchayat).values_list('village').distinct()
    village=[i[0] for i in village]
    return render(request,"load_village.html",{'village':village})

@login_required
def load_constency(request):
    village=request.GET.get('village')
    constency=WaterPlantLoc.objects.filter(village=village).values_list('constency').distinct()
    constency=[i[0] for i in constency]
    print(constency)
    return render(request,"load_constency.html",{'constency':constency})


def get_filterd_loc(m1,m2,m3,m4,m5):
    if(m1=="NULL" and m2=="NULL" and m3=="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.all()
    elif(m1=="NULL" and m2=="NULL" and m3=="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(constency=m5)
    elif(m1=="NULL" and m2=="NULL" and m3=="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(village=m4)
    elif(m1=="NULL" and m2=="NULL" and m3=="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(village=m4,constency=m5)
    elif(m1=="NULL" and m2=="NULL" and m3!="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(gram_panchayat=m3)
    elif(m1=="NULL" and m2=="NULL" and m3!="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(gram_panchayat=m3,constency=m5)
    elif(m1=="NULL" and m2=="NULL" and m3!="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(gram_panchayat=m3,village=m4)
    elif(m1=="NULL" and m2=="NULL" and m3!="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(gram_panchayat=m3,village=m4,constency=m5)
    elif(m1=="NULL" and m2!="NULL" and m3=="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2)
    elif(m1=="NULL" and m2!="NULL" and m3=="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,constency=m5)
    elif(m1=="NULL" and m2!="NULL" and m3=="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,village=m4)
    elif(m1=="NULL" and m2!="NULL" and m3=="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,village=m4,constency=m5)
    elif(m1=="NULL" and m2!="NULL" and m3!="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,gram_panchayat=m3)
    elif(m1=="NULL" and m2!="NULL" and m3!="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,gram_panchayat=m3,constency=m5)
    elif(m1=="NULL" and m2!="NULL" and m3!="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,gram_panchayat=m3,village=m4)
    elif(m1=="NULL" and m2!="NULL" and m3!="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(mandal=m2,gram_panchayat=m3,village=m4,constency=m5)
    elif(m1!="NULL" and m2=="NULL" and m3=="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1)
    elif(m1!="NULL" and m2=="NULL" and m3=="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,constency=m5)
    elif(m1!="NULL" and m2=="NULL" and m3=="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,village=m4)
    elif(m1!="NULL" and m2=="NULL" and m3=="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,village=m4,constency=m5)
    elif(m1!="NULL" and m2=="NULL" and m3!="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,gram_panchayat=m3)
    elif(m1!="NULL" and m2=="NULL" and m3!="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,gram_panchayat=m3,constency=m5)
    elif(m1!="NULL" and m2=="NULL" and m3!="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(disteic=m1,gram_panchayat=m3,village=m4)
    elif(m1!="NULL" and m2=="NULL" and m3!="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,gram_panchayat=m3,village=m4,constency=m5)
    elif(m1!="NULL" and m2!="NULL" and m3=="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2)
    elif(m1!="NULL" and m2!="NULL" and m3=="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,constency=m5)
    elif(m1!="NULL" and m2!="NULL" and m3=="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,village=m4)
    elif(m1!="NULL" and m2!="NULL" and m3=="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,village=m4,constency=m5)
    elif(m1!="NULL" and m2!="NULL" and m3!="NULL" and m4=="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,gram_panchayat=m3)
    elif(m1!="NULL" and m2!="NULL" and m3!="NULL" and m4=="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,gram_panchayat=m3,constency=m5)
    elif(m1!="NULL" and m2!="NULL" and m3!="NULL" and m4!="NULL" and m5=="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,gram_panchayat=m3,village=m4)
    elif(m1!="NULL" and m2!="NULL" and m3!="NULL" and m4!="NULL" and m5!="NULL"):
        return WaterPlantLoc.objects.filter(district=m1,mandal=m2,gram_panchayat=m3,village=m4,constency=m5)
    else:
        return WaterPlantLoc.objects.all()



@login_required
def ajax_filtertable_new(request):
    district=request.GET.get('district')
    mandal=request.GET.get('mandal')
    gram_panchayat=request.GET.get('gram_panchayat')
    village=request.GET.get('village')
    constency=request.GET.get('constency')
    locs=get_filterd_loc(district,mandal,gram_panchayat,village,constency)
    new_wp=WaterPlant.objects.filter(loc__in=locs,is_amc=False)
    return render(request,'ajax_new_table.html',{'data':new_wp})


@login_required
def ajax_filtertable_old(request):
    district=request.GET.get('district')
    mandal=request.GET.get('mandal')
    gram_panchayat=request.GET.get('gram_panchayat')
    village=request.GET.get('village')
    constency=request.GET.get('constency')
    locs=get_filterd_loc(district,mandal,gram_panchayat,village,constency)
    new_wp=WaterPlant.objects.filter(loc__in=locs,is_amc=True)
    print(new_wp)
    return render(request,'ajax_new_table.html',{'data':new_wp})


@login_required
def AddConsumbles(request):
    if "GET"==request.method:
        context=get_set_of_locs_inWP(request.user)
        return render(request,'AddConsumables.html',context)
    else:
        district=request.POST.get('district')
        mandal=request.POST.get('mandal')
        gram_panchayat=request.POST.get('gram_panchayat')
        village=request.POST.get('village')
        constency=request.POST.get('constency')
        filters=request.POST.get('filters')
        liquid_case=request.POST.get('liquid_case')
        date=request.POST.get('date')
        context=get_set_of_locs_inWP(request.user)
        context['error_message']=[]
        context['success_message']=[]
        try:
            date=dt.strptime(date,"%Y-%m-%d")#datetype format
        except:
            context['error_message'].append('Please check the date')
        if(not filters.isdigit() or not liquid_case.isdigit() or int(filters)<0 or int(liquid_case)<0):
            context['error_message'].append('filters and liquid Case Should be only numbers and greater than 0')
        try:
            locs=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
            wp=WaterPlant.objects.get(loc=locs)
        except:
            context['error_message'].append('There is no Water Plant for the given location')
        if(len(context['error_message'])==0):
            c=Consumables(WP=wp,filters=filters,liquid_case=liquid_case,date=date)
            c.save()
            context['success_message'].append('Consumable successfully added')
            return render(request,'AddConsumables.html',context)
        else:
            return render(request,'AddConsumables.html',context)


@login_required
def load_mandal_wp(request):
    district=request.GET.get('district')
    user=request.GET.get('user')
    user=User.objects.get(pk=int(user))
    if(user.is_superuser):
        locs=WaterPlant.objects.all().values_list('loc').distinct()
        mandals=WaterPlantLoc.objects.filter(district=district).values_list('mandal').distinct()
        mandals=set([i[0] for i in mandals])
        mandal_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).mandal for i in locs])
        mandals=mandal_inWP.intersection(mandals)
        return render(request,"load_mandal.html",{'mandal':mandals})
    else:
        locs=WaterPlant.objects.filter(incharge=user).values_list('loc').distinct()
        mandals=WaterPlantLoc.objects.filter(district=district).values_list('mandal').distinct()
        mandals=set([i[0] for i in mandals])
        mandal_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).mandal for i in locs])
        mandals=mandal_inWP.intersection(mandals)
        return render(request,"load_mandal.html",{'mandal':mandals})

@login_required
def load_gram_panchayat_wp(request):
    mandal=request.GET.get('mandal')
    user=request.GET.get('user')
    user=User.objects.get(pk=int(user))
    if(user.is_superuser):
        locs=WaterPlant.objects.all().values_list('loc').distinct()
        gram_panchayat=WaterPlantLoc.objects.filter(mandal=mandal).values_list('gram_panchayat').distinct()
        gram_panchayat=set([i[0] for i in gram_panchayat])
        gram_panchayat_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).gram_panchayat for i in locs])
        gram_panchayat=gram_panchayat_inWP.intersection(gram_panchayat)
        
        return render(request,"load_gram_panchayat.html",{'gram_panchayat':gram_panchayat})
    else:
        locs=WaterPlant.objects.filter(incharge=user).values_list('loc').distinct()
        gram_panchayat=WaterPlantLoc.objects.filter(mandal=mandal).values_list('gram_panchayat').distinct()
        gram_panchayat=set([i[0] for i in gram_panchayat])
        gram_panchayat_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).gram_panchayat for i in locs])
        gram_panchayat=gram_panchayat_inWP.intersection(gram_panchayat)
        
        return render(request,"load_gram_panchayat.html",{'gram_panchayat':gram_panchayat})

@login_required
def load_village_wp(request):
    gram_panchayat=request.GET.get('gram_panchayat')
    user=request.GET.get('user')
    user=User.objects.get(pk=int(user))
    if(user.is_superuser):
        locs=WaterPlant.objects.all().values_list('loc').distinct()
        village=WaterPlantLoc.objects.filter(gram_panchayat=gram_panchayat).values_list('village').distinct()
        village=set([i[0] for i in village])
        village_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).village for i in locs])
        village=village_inWP.intersection(village)
        return render(request,"load_village.html",{'village':village})
    else:
        locs=WaterPlant.objects.filter(incharge=user).values_list('loc').distinct()
        village=WaterPlantLoc.objects.filter(gram_panchayat=gram_panchayat).values_list('village').distinct()
        village=set([i[0] for i in village])
        village_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).village for i in locs])
        village=village_inWP.intersection(village)
        return render(request,"load_village.html",{'village':village})

@login_required
def load_constency_wp(request):
    village=request.GET.get('village')
    user=request.GET.get('user')
    user=User.objects.get(pk=int(user))
    if(user.is_superuser):
        locs=WaterPlant.objects.all().values_list('loc').distinct()
        constency=WaterPlantLoc.objects.filter(village=village).values_list('constency').distinct()
        constency=[i[0] for i in constency]
        constency_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).constency for i in locs])
        constency=constency_inWP.intersection(constency)
        return render(request,"load_constency.html",{'constency':constency})
    else:
        locs=WaterPlant.objects.filter(incharge=user).values_list('loc').distinct()
        constency=WaterPlantLoc.objects.filter(village=village).values_list('constency').distinct()
        constency=[i[0] for i in constency]
        constency_inWP=set([WaterPlantLoc.objects.get(pk=i[0]).constency for i in locs])
        constency=constency_inWP.intersection(constency)
        return render(request,"load_constency.html",{'constency':constency})


@login_required
def consumables_list(request):
    context=get_set_of_locs_inWP(request.user)
    return render(request,'ConsumablesList.html',context)


@login_required
def table_consumable_list(request):
    district=request.GET.get('district')
    mandal=request.GET.get('mandal')
    gram_panchayat=request.GET.get('gram_panchayat')
    village=request.GET.get('village')
    constency=request.GET.get('constency')
    locs=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
    new_wp=WaterPlant.objects.get(loc=locs)
    data=Consumables.objects.filter(WP=new_wp).order_by('date')
    return render(request,'ajax_consumable_db.html',{'data':data})

    

@login_required
def ConsumablesDelete(request,pk):
    c=Consumables.objects.get(pk=pk)
    c.delete()
    context=get_set_of_locs_inWP(request.user)
    context['success_message']='Successfully deleted'
    return render(request,'ConsumablesList.html',context)


@login_required
@superuser
def cost_management(request):
    if "GET"==request.method:
        data=Cost.objects.all().order_by('date')
        return render(request,'cost_management.html',{'data':data})
    else:
        context={}
        data=Cost.objects.all().order_by('date')
        context['data']=data
        filters=request.POST.get('filter')
        liquids=request.POST.get('liquid')
        date=request.POST.get('date')
        context['error_message']=[]
        context['success_message']=[]
        try:
            date=dt.strptime(date,"%Y-%m-%d")#datetype format
        except:
            context['error_message'].append('Please check the date')
        try:
            if(float(filters)<0 or float(liquids)<0):
                context['error_message'].append('Please Fill the details properly')
        except:
            context['error_message'].append('Please Fill the details properly')

        if(len(context['error_message'])>0):
            return render(request,'cost_management.html',context)
        else:
            c=Cost(filters=filters,liquid=liquids,date=date)
            c.save()
            data=Cost.objects.all().order_by('date')
            context['data']=data
            context['success_message'].append('Updated Successfully')
            return render(request,'cost_management.html',context)
        

@login_required
@superuser
def deleteCost(request,pk):
    c=Cost.objects.get(pk=pk)
    c.delete()
    data=Cost.objects.all()
    return render(request,'cost_management.html',{'data':data,'success_message':['Successfully Deleted']})


@login_required
def ajax_get_wp_name(request):
    district=request.GET.get('district')
    mandal=request.GET.get('mandal')
    gram_panchayat=request.GET.get('gram_panchayat')
    village=request.GET.get('village')
    constency=request.GET.get('constency')
    locs=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
    try:
        new_wp=WaterPlant.objects.get(loc=locs)
        return render(request,'ajax_get_wp_name.html',{'data':new_wp.loc.village})
        print(new_wp.loc.village)
    except:
        return render(request,'ajax_get_wp_name.html',{'data':"None"})

@login_required
def AddRepairParts(request):
    if "GET"==request.method:
        context=get_set_of_locs_inWP(request.user)
        return render(request,'repair_parts.html',context)
    else:
        context=get_set_of_locs_inWP(request.user)
        parts=request.POST.get('parts')
        description=request.POST.get('description')
        amount=request.POST.get('amount')
        district=request.POST.get('district')
        mandal=request.POST.get('mandal')
        gram_panchayat=request.POST.get('gram_panchayat')
        village=request.POST.get('village')
        constency=request.POST.get('constency')
        context['success_message']=[]
        context['error_message']=[]
        try:
            d=float(amount)
        except:
            context['error_message'].append('Amount should be in digits or decimal')
        locs=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
        wp=WaterPlant.objects.get(loc=locs)
        if(len(context['error_message'])>0):
            return render(request,'repair_parts.html',context)
        else:
            rp=repair_parts(WP=wp,parts=parts,description=description,amount=amount)
            rp.save()
            context['success_message'].append('Repair Part Successfully added')
            return render(request,'repair_parts.html',context)



           
    

@login_required
def RepairPartsDB(request):
    context=get_set_of_locs_inWP(request.user)
    return render(request,'repair_partsDB.html',context)

@login_required
def table_repair_parts_data(request):
    district=request.GET.get('district')
    mandal=request.GET.get('mandal')
    gram_panchayat=request.GET.get('gram_panchayat')
    village=request.GET.get('village')
    constency=request.GET.get('constency')
    locs=WaterPlantLoc.objects.get(district=district,mandal=mandal,gram_panchayat=gram_panchayat,village=village,constency=constency)
    new_wp=WaterPlant.objects.get(loc=locs)
    data=repair_parts.objects.filter(WP=new_wp)
    return render(request,'ajax_repair_list_db.html',{'data':data})

@login_required
def deleteRepairParts(request,pk):
    d=repair_parts.objects.get(pk=pk)
    wp=d.WP
    data=repair_parts.objects.filter(WP=wp)
    d.delete()
    context=get_set_of_locs_inWP(request.user)
    context['data']=data
    context['success_message']='Successfully deleted'
    return render(request,'repair_partsDB.html',context)

class plant_feat:
    def __init__(self,c):
        self.filters=int(c.filters)
        self.liquid_case=int(c.liquid_case)
    
    def add(self,c):
        self.filters=self.filters+int(c.filters)
        self.liquid_case=self.liquid_case+int(c.liquid_case)

class consumable_report:
    def __init__(self,c_list,year,wp_name):
        self.c_list=c_list
        self.year=year
        self.total_filter=0
        self.total_liquid_case=0
        self.plant_name=wp_name
        self.Jan=None
        self.Feb=None
        self.March=None
        self.April=None
        self.May=None
        self.June=None
        self.July=None
        self.Aug=None
        self.Sept=None
        self.Oct=None
        self.Nov=None
        self.Dec=None
        for i in c_list:
            if(i.date.year==self.year):
                if(i.date.month==1):
                    if(self.Jan):
                        self.Jan.add(i)
                    else:
                        self.Jan=plant_feat(i)
                elif(i.date.month==2):
                    if(self.Feb):
                        self.Feb.add(i)
                    else:
                        self.Feb=plant_feat(i)
                elif(i.date.month==3):
                    if(self.March):
                        self.March.add(i)
                    else:
                        self.March=plant_feat(i)
                elif(i.date.month==4):
                    if(self.April):
                        self.April.add(i)
                    else:
                        self.April=plant_feat(i)
                elif(i.date.month==5):
                    if(self.May):
                        self.May.add(i)
                    else:
                        self.May=plant_feat(i)
                elif(i.date.month==6):
                    if(self.June):
                        self.June.add(i)
                    else:
                        self.June=plant_feat(i)
                elif(i.date.month==7):
                    if(self.July):
                        self.July.add(i)
                    else:
                        self.July=plant_feat(i)

                elif(i.date.month==8):
                    if(self.Aug):
                        self.Aug.add(i)
                    else:
                        self.Aug=plant_feat(i)


                elif(i.date.month==9):
                    if(self.Sept):
                        self.Sept.add(i)
                    else:
                        self.Sept=plant_feat(i)

                elif(i.date.month==10):
                    if(self.Oct):
                        self.Oct.add(i)
                    else:
                        self.Oct=plant_feat(i)
                elif(i.date.month==11):
                    if(self.Nov):
                        self.Nov.add(i)
                    else:
                        self.Nov=plant_feat(i)
                elif(i.date.month==12):
                    if(self.Dec):
                        self.Dec.add(i)
                    else:
                        self.Dec=plant_feat(i)
                self.total_filter=self.total_filter+int(i.filters)
                self.total_liquid_case=self.total_liquid_case+int(i.liquid_case)




def get_list_of_years(c_list):
    years=[]
    for i in c_list:
        if(i.date.year not in years):
            years.append(i.date.year)
    return years

@login_required
@superuser
def view_consumable_track(request):
    wps=WaterPlant.objects.all()
    data=[]
    for i in wps:
        c_list=Consumables.objects.filter(WP=i)
        year=get_list_of_years(c_list)
        try:
            year=year[0]
        except:
            year=2018
        wp_name=i
        report=consumable_report(c_list,year,wp_name)
        data.append(report)
    print(data[0].Jan)    
    return render(request,'view_consumable_track.html',{'data':data})

@login_required
@superuser
def ajax_view_consumable_track(request):
    wps=WaterPlant.objects.all()
    year=request.GET.get('year')
    print(year)
    year=int(year)
    data=[]
    for i in wps:
        c_list=Consumables.objects.filter(WP=i)
        wp_name=str(i)
        report=consumable_report(c_list,year,wp_name)
        data.append(report)    
    return render(request,'ajax_view_consumable_track.html',{'data':data})


@login_required
@superuser
def view_consumable_track_yearly(request):
    wps=WaterPlant.objects.all()
    data=[]
    years=get_years_fu()
    for i in wps:
        c_list=Consumables.objects.filter(WP=i)
        wp_name=i
        reports=[]
        for i in years:
            report=consumable_report(c_list,i,wp_name)
            reports.append(report)
        data.append(reports)
    return render(request,'view_consumable_track_yearly.html',{'data':data,'years':years})

def get_years_fu():
    obs=Consumables.objects.all().order_by('date')
    min_year_ob,max_year_ob=obs[0],obs[len(obs)-1]
    min_year=min_year_ob.date.year
    max_year=max_year_ob.date.year
    year=[]
    for i in range(min_year,max_year+1):
        year.append(i)
    return year

def get_years(request):
    year=get_years_fu()
    data=''
    for i in year:
        data=data+'<option>'+str(i)+'</option>'
    return HttpResponse(data)

def get_costing_obj(cmble,costing_list):
    costing_obj=None
    for i in range(len(costing_list)-1):
        if(cmble.date>=costing_list[i].date and cmble.date<costing_list[i+1].date):
            costing_obj=costing_list[i]
            break
    return costing_obj
    


class financial_plant_feat:
    def __init__(self,c,cost):
        self.filters=int(c.filters)*float(cost.filters)
        self.liquid_case=int(c.liquid_case)*float(cost.liquid)
        self.costing_obj=cost

    def add(self,c,cost):
        self.filters=self.filters+int(c.filters)*float(cost.filters)
        self.liquid_case=self.liquid_case+int(c.liquid_case)*float(cost.liquid)

class financial_report:
    def __init__(self,c_list,year,wp_name,costing_list):
        self.c_list=c_list
        self.year=year
        self.total_filter=0
        self.total_liquid_case=0
        self.filters_cost=0
        self.liquid_cost=0
        self.plant_name=wp_name
        self.pk=wp_name.pk
        self.Jan=None
        self.Feb=None
        self.March=None
        self.April=None
        self.May=None
        self.June=None
        self.July=None
        self.Aug=None
        self.Sept=None
        self.Oct=None
        self.Nov=None
        self.Dec=None
        for i in c_list:
            cost_obj=get_costing_obj(i,costing_list)
            if(i.date.year==self.year):
                if(i.date.month==1):
                    if(self.Jan):
                        self.Jan.add(i,cost_obj)

                    else:
                        self.Jan=financial_plant_feat(i,cost_obj)
                elif(i.date.month==2):
                    if(self.Feb):
                        self.Feb.add(i,cost_obj)
                    else:
                        self.Feb=financial_plant_feat(i,cost_obj)
                elif(i.date.month==3):
                    if(self.March):
                        self.March.add(i,cost_obj)
                    else:
                        self.March=financial_plant_feat(i,cost_obj)
                elif(i.date.month==4):
                    if(self.April):
                        self.April.add(i,cost_obj)
                    else:
                        self.April=financial_plant_feat(i,cost_obj)
                elif(i.date.month==5):
                    if(self.May):
                        self.May.add(i,cost_obj)
                    else:
                        self.May=financial_plant_feat(i,cost_obj)
                elif(i.date.month==6):
                    if(self.June):
                        self.June.add(i,cost_obj)
                    else:
                        self.June=financial_plant_feat(i,cost_obj)
                elif(i.date.month==7):
                    if(self.July):
                        self.July.add(i,cost_obj)
                    else:
                        self.July=financial_plant_feat(i,cost_obj)

                elif(i.date.month==8):
                    if(self.Aug):
                        self.Aug.add(i,cost_obj)
                    else:
                        self.Aug=financial_plant_feat(i,cost_obj)


                elif(i.date.month==9):
                    if(self.Sept):
                        self.Sept.add(i,cost_obj)
                    else:
                        self.Sept=financial_plant_feat(i,cost_obj)

                elif(i.date.month==10):
                    if(self.Oct):
                        self.Oct.add(i,cost_obj)
                    else:
                        self.Oct=financial_plant_feat(i,cost_obj)
                elif(i.date.month==11):
                    if(self.Nov):
                        self.Nov.add(i,cost_obj)
                    else:
                        self.Nov=financial_plant_feat(i,cost_obj)
                elif(i.date.month==12):
                    if(self.Dec):
                        self.Dec.add(i,cost_obj)
                    else:
                        self.Dec=financial_plant_feat(i,cost_obj)
                self.total_filter=self.total_filter+int(i.filters)
                self.total_liquid_case=self.total_liquid_case+int(i.liquid_case)
                self.filters_cost=self.filters_cost+int(i.filters)*float(cost_obj.filters)
                self.liquid_cost=self.liquid_cost+int(i.liquid_case)*float(cost_obj.liquid)



@login_required
@superuser
def view_financial_track(request):
    wps=WaterPlant.objects.all()
    data=[]
    cost_list=Cost.objects.all().order_by('date')
    for i in wps:
        c_list=Consumables.objects.filter(WP=i)
        year=get_list_of_years(c_list)
        try:
            year=year[0]
        except:
            year=2018
        report=financial_report(c_list,year,i,cost_list)
        data.append(report)
    print(data)    
    return render(request,'view_financial_track.html',{'data':data})


@login_required
@superuser
def ajax_view_financial_track(request):
    wps=WaterPlant.objects.all()
    year=request.GET.get('year')
    year=int(year)
    data=[]
    cost_list=Cost.objects.all().order_by('date')
    for i in wps:
        c_list=Consumables.objects.filter(WP=i)
        report=financial_report(c_list,year,i,cost_list)
        data.append(report)    
    return render(request,'ajax_view_financial_track.html',{'data':data})




@login_required
@superuser
def view_financial_track_yearly(request):
    wps=WaterPlant.objects.all()
    data=[]
    years=get_years_fu()
    cost_list=Cost.objects.all().order_by('date')
    for i in wps:
        c_list=Consumables.objects.filter(WP=i)
        wp_name=i
        reports=[]
        for i in years:
            report=financial_report(c_list,i,wp_name,cost_list)
            reports.append(report)
        data.append(reports)
    return render(request,'view_financial_track_yearly.html',{'data':data,'years':years})



def get_graph_dict(report):
    if(report.Jan):
        m1={'y':'Jan','a':report.Jan.filters,'b':report.Jan.liquid_case}
    else:
        m1={'y':'Jan','a':0,'b':0}
    if(report.Feb):
        m2={'y':'Feb','a':report.Feb.filters,'b':report.Feb.liquid_case}
    else:
        m2={'y':'Feb','a':0,'b':0}
    if(report.March):
        m3={'y':'March','a':report.March.filters,'b':report.March.liquid_case}
    else:
        m3={'y':'March','a':0,'b':0}
    if(report.April):
        m4={'y':'April','a':report.April.filters,'b':report.April.liquid_case}
    else:
        m4={'y':'April','a':0,'b':0}
    if(report.May):
        m5={'y':'May','a':report.May.filters,'b':report.May.liquid_case}
    else:
        m5={'y':'May','a':0,'b':0}
    if(report.June):
        m6={'y':'June','a':report.June.filters,'b':report.June.liquid_case}
    else:
        m6={'y':'June','a':0,'b':0}
    if(report.July):
        m7={'y':'July','a':report.July.filters,'b':report.July.liquid_case}
    else:
        m7={'y':'July','a':0,'b':0}
    if(report.Aug):
        m8={'y':'Aug','a':report.Aug.filters,'b':report.Aug.liquid_case}
    else:
        m8={'y':'Aug','a':0,'b':0}
    if(report.Sept):
        m9={'y':'Sept','a':report.Sept.filters,'b':report.Sept.liquid_case}
    else:
        m9={'y':'Sept','a':0,'b':0}
    if(report.Oct):
        m10={'y':'Oct','a':report.Oct.filters,'b':report.Oct.liquid_case}
    else:
        m10={'y':'Oct','a':0,'b':0}
    if(report.Nov):
        m11={'y':'Nov','a':report.Nov.filters,'b':report.Nov.liquid_case}
    else:
        m11={'y':'Nov','a':0,'b':0}
    if(report.Dec):
        m12={'y':'Dec','a':report.Dec.filters,'b':report.Dec.liquid_case}
    else:
        m12={'y':'Dec','a':0,'b':0}
    data=[m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12]
    return data





@login_required
@superuser
def monthly_consumable_bar_gph(request):
    year=request.GET.get('year')
    year=int(year) #dynamic year
    wp=request.GET.get('wp')
    loc=WaterPlantLoc.objects.get(village=wp)
    wps=WaterPlant.objects.get(loc=loc) #dyanamic water plant
    c_list=Consumables.objects.filter(WP=wps)
    wp_name=str(wps)
    report=consumable_report(c_list,year,wp_name)
    data=get_graph_dict(report)
    return JsonResponse(data,safe=False)

@login_required
def get_water_plants(request):
    wps=Consumables.objects.all().values_list('WP').distinct()
    wps=[i[0] for i in wps]
    wps=WaterPlant.objects.filter(pk__in=wps)
    data='<option>-----</option>'
    for i in wps:
        data=data+'<option values="'+str(i.pk)+'">'+str(i)+'</option>'
    return HttpResponse(data)

@login_required
def monthly_bar_graph(request):
    year=request.GET.get('year')
    wp=request.GET.get('wp')
    return render(request,'monthly_bar_graph.html',{'year':year,'wp':wp})


@login_required
def monthly_financial_bar_gph(request):
    year=request.GET.get('year')
    year=int(year) #dynamic year
    wp=request.GET.get('wp')
    loc=WaterPlantLoc.objects.get(village=wp)
    wps=WaterPlant.objects.get(loc=loc) #dyanamic water plant
    c_list=Consumables.objects.filter(WP=wps)
    cost=Cost.objects.all().order_by('date')
    wp_name=wps
    report=financial_report(c_list,year,wp_name,cost)
    data=get_graph_dict(report)
    return JsonResponse(data,safe=False)

@login_required
def monthly_bar_graph_f(request):
    year=request.GET.get('year')
    wp=request.GET.get('wp')
    return render(request,'monthly_bar_graph_f.html',{'year':year,'wp':wp})


@login_required
def cost_management_graph(request):
    data=[]
    cost=Cost.objects.all().order_by('date')
    for i in cost:
        d={}
        d['y']=i.date
        d['a']=i.filters
        d['b']=i.liquid
        data.append(d) 
    return JsonResponse(data,safe=False)   


def get_years_by_wp(wp):
    obs=Consumables.objects.filter(WP=wp).order_by('date')
    try:
        min_year_ob,max_year_ob=obs[0],obs[len(obs)-1]
        min_year=min_year_ob.date.year
        max_year=max_year_ob.date.year
        year=[]
        for i in range(min_year,max_year+1):
            year.append(i)
        return(year)
    except:
        return None 
    


def render_to_pdf(template_src,context):
    template=get_template(template_src)
    html=template.render(context)
    result=BytesIO()
    pdf=pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")),result)
    if not pdf.err:
        return HttpResponse(result.getvalue(),content='application/pdf')
    else:
        return None

@login_required
@superuser
def complete_water_plant_report(request,pk):
    #For Basic Information
    wp=WaterPlant.objects.get(pk=pk)# Taking Example as Plant V1
    ConsumableReport=[]
    #Consumable Track
    years=get_years_by_wp(wp.pk)
    c_list=Consumables.objects.filter(WP=wp.pk)
    for i in years:
        report=consumable_report(c_list,i,str(wp))
        ConsumableReport.append(report)
    #Financial Report
    cost=Cost.objects.all().order_by('date')
    FinancialReport=[]
    for i in years:
        report=financial_report(c_list,i,wp,cost)
        FinancialReport.append(report)
    #Repair Parts
    RepairParts=repair_parts.objects.filter(WP=wp.pk)
    cost=0
    for i in RepairParts:
        cost=cost+float(i.amount)

    total=0
    for i in FinancialReport:
        total=total+i.filters_cost+i.liquid_cost
    total=total+cost

    context={
        'wp':wp,
        'ConsumableReport':ConsumableReport,
        'FinancialReport':FinancialReport,
        'RepairParts':RepairParts,
        'cost':cost,
        'total':total
    }
    return render(request,'complete_water_plant_report.html',context)

@login_required
@superuser
def wpnew_export(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="WaterPlantNew.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('WaterPlantNew')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['District','Mandal','Gram Panchayat','Village','Constency','Population','Capacity','Date','Contact Person','Pnone Number','Operator Name','Pnone Number']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows=WaterPlant.objects.filter(is_amc=False)
    for i in rows:
        row=[i.loc.district,i.loc.mandal,i.loc.gram_panchayat,i.loc.village,i.loc.constency,i.populations,i.capacity,i.date,i.contact_person,i.contact_number,i.operator_name,i.operator_phone_number]
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response

@login_required
@superuser
def wpamc_export(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="WaterPlantAMC.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('WaterPlantAMC')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['District','Mandal','Gram Panchayat','Village','Constency','Population','Capacity','Date','Contact Person','Pnone Number','Operator Name','Pnone Number']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    rows=WaterPlant.objects.filter(is_amc=True)
    for i in rows:
        row=[i.loc.district,i.loc.mandal,i.loc.gram_panchayat,i.loc.village,i.loc.constency,i.populations,i.capacity,i.date,i.contact_person,i.contact_number,i.operator_name,i.operator_phone_number]
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response


@login_required
@superuser
def detailed_FP(request,pk):
    #For Basic Information
    wp=WaterPlant.objects.get(pk=pk)# Taking Example as Plant V1
    ConsumableReport=[]
    #Consumable Track
    years=get_years_by_wp(wp.pk)
    c_list=Consumables.objects.filter(WP=wp.pk)
    if(years):
        for i in years:
            report=consumable_report(c_list,i,str(wp))
            ConsumableReport.append(report)
    #Financial Report
    cost=Cost.objects.all().order_by('date')
    print(cost)
    FinancialReport=[]
    if(years):
        for i in years:
            report=financial_report(c_list,i,wp,cost)
            FinancialReport.append(report)
    #Repair Parts
    total=0
    for i in FinancialReport:
        total=total+i.filters_cost+i.liquid_cost
    context={
        'wp':wp,
        'FinancialReport':FinancialReport,
        'total':total,
    }
    return render(request,'DetailFinancialReport.html',context)


@login_required
@superuser
def complete_financial_report(request):
    wp=WaterPlant.objects.all()
    TotalReport=[]
    cost=Cost.objects.all().order_by('date')
    for i in wp:
        years=get_years_by_wp(i.pk)
        c_list=Consumables.objects.filter(WP=i.pk)
        FinancialReport=[]
        if(years):
            for j in years:
                report=financial_report(c_list,j,i,cost)
                FinancialReport.append(report)
            TotalReport.append(FinancialReport)
    return render(request,'CompleteFinancialReport.html',{'TotalReport':TotalReport})

@login_required
@superuser
def ReportGenerator(request):
    wps=WaterPlant.objects.all()
    return render(request,'WaterPlantReport.html',{'wps':wps})



@login_required
def NotificationManager(request):
    if(request.user.is_superuser):
        wps=WaterPlant.objects.all()
    else:
        wps=WaterPlant.objects.filter(incharge=request.user)
    Notify=[]
    for i in wps:
        c_list=Consumables.objects.filter(WP=i).order_by('date')
        if(len(c_list)):
            latest_sub=c_list[len(c_list)-1].date
            todays_date=dt.now().date()
            diff=todays_date-latest_sub
            if(diff.days>30):
                Notify.append([i,latest_sub,diff.days,True])
        else:
            latest_sub=i.date
            todays_date=dt.now().date()
            diff=todays_date-latest_sub
            Notify.append([i,latest_sub,diff,False])
    return render(request,'ajax_notifications.html',{'data':Notify})


            
@login_required
def AddConsumables_withpk(request,pk):
    wp=WaterPlant.objects.get(pk=pk)
    return render(request,'AddConsumables_withPk.html',{'wp':wp})

@login_required
def AddConsumblesPK(request,pk):
    if "GET"==request.method:
        return HttpResponse("<h1>Not Found</h1>")
    else:
        context={}
        wp=WaterPlant.objects.get(pk=pk)
        filters=request.POST.get('filters')
        liquid_case=request.POST.get('liquid_case')
        date=request.POST.get('date')
        context['error_message']=[]
        context['success_message']=[]
        wp1=WaterPlant.objects.all()
        try:
            date=dt.strptime(date,"%Y-%m-%d")#datetype format
        except:
            context['error_message'].append('Please check the date')
        if(not filters.isdigit() or not liquid_case.isdigit() or int(filters)<0 or int(liquid_case)<0):
            context['error_message'].append('filters and liquid Case Should be only numbers and greater than 0')
        if(len(context['error_message'])==0):
            c=Consumables(WP=wp,filters=filters,liquid_case=liquid_case,date=date)
            c.save()
            context['success_message'].append('Consumable successfully added')
            if(request.user.is_superuser):
                return render(request,'index.html',{'total':len(wp1)})
            else:
                return render(request,'dashboard_incharge.html')
        else:
            if(request.user.is_superuser):
                return render(request,'index.html',{'total':len(wp1)})
            else:
                return render(request,'dashboard_incharge.html')
    
@login_required
@superuser
def ReportPage(request):
    return render(request,'ReportPage.html')

@login_required
@superuser
def SettingPage(request):
    return render(request,'SettingPage.html')

@login_required
@superuser
def WPPage(request):
    return render(request,'WaterPlantPage.html')

class InchargeCreateView(CreateView):
    form_class = InchargeForm
    template_name = 'InchargeCreate.html'

##Code By:

# Shashwat Sanket --> Created 07-01-2019

