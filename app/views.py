from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from app.models import *
from app.handlers import save_signature_from_base64
from .forms import AdminRegistrationForm, AssignPostForm, CustomUserForm, NameChildPostForm, EditPostForm, UserSearchForm, WorkaroundForm, SheetFormSet
from django.http import JsonResponse
from .models import WorkaroundModel, WorkaroundSheetModel, SignatureModel, StatusModel, PostChildModel
from django.db.models import Count, Q
from django.contrib import messages
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from django.conf import settings
from django.contrib.auth import logout
from django.utils.safestring import mark_safe
from django.db.models import Count, Q, OuterRef, Subquery, Exists


def get_roles(req):
    department_id = req.GET.get('department_id')
    roles = RoleModel.objects.filter(department_id=department_id).values('id', 'name')
    return JsonResponse({'roles': list(roles)})


class MainView(View):
    """
    Получение главной страницы
    """
    def MainPage(req):
        # Статистика
        user_count = CustomUser.objects.count()
        workaround_count = WorkaroundModel.objects.count()
        completed_workaround_count = WorkaroundModel.objects.filter(status__name="Завершен").count()
        department_count = DepartmentModel.objects.count()

        context = {
            'user_count': user_count,
            'workaround_count': workaround_count,
            'completed_workaround_count': completed_workaround_count,
            'department_count': department_count,
        }
        return render(req, 'index.html', context)
    


class Helpers:
    """
    Здесь вспомогательные функцииЮ заполнение БД и создание обходного листа
    """
    @staticmethod
    def RoleCreateFunc(arr, model):
        for item in arr:
            if not model.objects.filter(name=item).exists():
                model.objects.create(name=item)

    @staticmethod
    def CreateObhodPagee(req, user_pk):
        user = CustomUser.objects.get(pk=user_pk)
        def WorkaroundSheetCreate(obhod_id):
            obj = NameChildPostModel.objects.all()
            order = 1  # Начинаем с порядка 1
            for item in obj:
                if item.name == "Зам директора по УР":
                    order = 999  # Максимальный порядок
                else:
                    order += 1
                sheet = WorkaroundSheetModel(
                    nameofpoint=item.name,
                    depart=item,
                    order=order,
                )
                sheet.save()
                SignatureModel.objects.create(
                    wam=WorkaroundModel.objects.get(pk=obhod_id),
                    wasm=sheet,
                )
            signUser = SignatureModel.objects.get(wasm__nameofpoint="Преподаватель", wam=obhod_id)
            signUser.user = user
            signUser.save()
        obhod_obj = WorkaroundModel.objects.create(user=user)
        WorkaroundSheetCreate(obhod_obj.pk)
        print('Обходной лист успешно создан')


class AdminView(View):
    """
    Здесь функции у администратора: действие с пользователями.
    """


    def generate_workaround_pdf(req, workaround_id):
        def check_all_signatures(sheets):
            missing_signatures = []
            for sheet in sheets:
                required_post = sheet.depart
                signer = CustomUser.objects.filter(postchildmodel__childpost=required_post).first()

                if signer:
                    signature_filename = f"{signer.username}_signature.png"
                    signature_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'signatures', signature_filename)
                    if not os.path.exists(signature_path):
                        missing_signatures.append(sheet.nameofpoint)
                else:
                    missing_signatures.append(sheet.nameofpoint)

            return (False, missing_signatures) if missing_signatures else (True, [])

        try:
            workaround = WorkaroundModel.objects.get(id=workaround_id)
            sheets = WorkaroundSheetModel.objects.filter(workaround=workaround).order_by('order')

            all_signatures_present, missing_signatures = check_all_signatures(sheets)
            if not all_signatures_present:
                return HttpResponse(
                    f"Отсутствуют подписи для: {', '.join(missing_signatures)}",
                    status=400
                )

            font_path_regular = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'times.ttf')
            font_path_bold = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'timesbd.ttf')

            pdfmetrics.registerFont(TTFont('TimesNewRoman', font_path_regular))
            pdfmetrics.registerFont(TTFont('TimesNewRoman-Bold', font_path_bold))

            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="workaround_{workaround_id}.pdf"'

            p = canvas.Canvas(response, pagesize=A4)
            width, height = A4

            rect_width = 350
            rect_height = 500
            rect_x = 30 * mm
            rect_y = (height - rect_height) / 2

            p.rect(rect_x, rect_y, rect_width, rect_height)
            p.setFont("TimesNewRoman", 12)

            # Заголовок
            p.setFont("TimesNewRoman-Bold", 14)
            workaround_type = workaround.typ.name.lower()

            if workaround_type == 'увольнение':
                title = "Обходной лист перед увольнением"
            elif workaround_type == 'перевод':
                title = "Обходной лист перед переводом"
            elif workaround_type == 'отпуск':
                title = "Обходной лист перед отпуском"
            else:
                title = "Обходной лист"

            title_width = p.stringWidth(title, "TimesNewRoman-Bold", 14)
            title_x = rect_x + (rect_width - title_width) / 2
            title_y = rect_y + rect_height - 10 * mm
            p.drawString(title_x, title_y, title)

            # Подзаголовок
            p.setFont("TimesNewRoman", 10)
            subtitle = "(сдается в приемную кабинет №211)"
            subtitle_width = p.stringWidth(subtitle, "TimesNewRoman", 10)
            subtitle_x = rect_x + (rect_width - subtitle_width) / 2
            subtitle_y = title_y - 5 * mm
            p.drawString(subtitle_x, subtitle_y, subtitle)

            y = subtitle_y - 15 * mm

            # Преподаватель
            p.setFont("TimesNewRoman-Bold", 12)
            p.drawString(rect_x + 10 * mm, y, "Преподаватель:")

            teacher = CustomUser.objects.filter(role__name="Преподаватель", pk=workaround.user.pk).first()
            if teacher:
                signature_filename = f"{teacher.username}_signature.png"
                signature_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'signatures', signature_filename)

                if os.path.exists(signature_path):
                    try:
                        p.setFont("TimesNewRoman", 10)
                        p.drawString(rect_x + 45 * mm, y, teacher.get_full_name())

                        p.drawImage(
                            signature_path,
                            rect_x + 55 * mm,
                            y - 10 * mm,
                            width=50 * mm,
                            height=20 * mm,
                            mask='auto'
                        )
                    except Exception as e:
                        print(f"Ошибка при вставке подписи преподавателя: {e}")
                        p.setFont("TimesNewRoman", 10)
                        p.drawString(rect_x + 45 * mm, y, "Ошибка загрузки подписи")
                else:
                    return HttpResponse('У данного пользователя нет подписи')
            else:
                p.setFont("TimesNewRoman", 10)
                p.drawString(rect_x + 45 * mm, y, "Преподаватель не найден")

            y -= 10 * mm

            # Пункты обходного листа
            for sheet in sheets:
                p.setFont("TimesNewRoman-Bold", 12)
                p.drawString(rect_x + 10 * mm, y, f"{sheet.nameofpoint}:")

                signer = CustomUser.objects.filter(postchildmodel__childpost=sheet.depart).first()
                if signer:
                    signature_filename = f"{signer.username}_signature.png"
                    signature_path = os.path.join(settings.BASE_DIR, 'app', 'static', 'signatures', signature_filename)

                    if os.path.exists(signature_path):
                        try:
                            p.setFont("TimesNewRoman", 10)
                            p.drawString(rect_x + 45 * mm, y, signer.get_full_name())

                            p.drawImage(
                                signature_path,
                                rect_x + 50 * mm,
                                y - 10 * mm,
                                width=50 * mm,
                                height=20 * mm,
                                mask='auto'
                            )
                        except Exception as e:
                            print(f"Ошибка при вставке подписи: {e}")
                            p.setFont("TimesNewRoman", 10)
                            p.drawString(rect_x + 60 * mm, y - 10 * mm, "Ошибка загрузки подписи")
                    else:
                        p.setFont("TimesNewRoman", 10)
                        p.drawString(rect_x + 40 * mm, y, "Файл подписи отсутствует")
                else:
                    p.setFont("TimesNewRoman", 10)
                    p.drawString(rect_x + 60 * mm, y - 10 * mm, "Подпись отсутствует")

                y -= 10 * mm

                if y < rect_y + 20 * mm:
                    p.showPage()
                    y = rect_y + rect_height - 30 * mm
                    p.setFont("TimesNewRoman", 12)

            p.showPage()
            p.save()

            return response

        except WorkaroundModel.DoesNotExist:
            return HttpResponse("Обходной лист не найден", status=404)
        except Exception as e:
            return HttpResponse(f"Ошибка при генерации PDF: {str(e)}", status=500)




    @login_required
    def list_users(req):
        page_n = 'list_users.html'
        if req.user.is_superuser:
            workarounds = CustomUser.objects.all()
            values = {
                "workarounds":workarounds,
            }
        return render(req,page_n, values)
    
    def admin_create_user(req):
        form = AdminRegistrationForm()
        if req.method == 'POST':
            print(req.POST)
            form = AdminRegistrationForm(req.POST)
            if form.is_valid():
                # Создаем пользователя, но пока не сохраняем в базу данных (commit=False)
                userr = form.save(commit=False)
                # Получаем выбранную роль из формы
                role = form.cleaned_data['role']
                userr.role = role
                userr.depart = DepartmentModel.objects.get(pk=req.POST['department'])
                # Сохраняем пользователя в базу данных
                userr.save()
                if role.name == "Ответственный":
                    childpost = form.cleaned_data['childpost']
                    # Создаем запись в модели PostChildModel
                    PostChildModel.objects.create(
                        user=userr,  # Связываем с созданным пользователем
                        childpost=childpost,  # Выбранная должность
                        post=DepartmentModel.objects.get(pk=req.POST['department'])
                    )
                # Перенаправляем администратора на страницу успешного создания
                return render(req, 'user/create_user.html', {'form': form, 'msg':'Успешно!'})
        else:
            form = AdminRegistrationForm()
        # Отображаем форму создания пользователя
        return render(req, 'user/create_user.html', {'form': form})

    @login_required
    def postsListFunc(req): 
        obj = None
        if req.method == "GET":
            obj = PostChildModel.objects.all()
            secondobj = NameChildPostModel.objects.all()
        values = {
            'list_posts':obj,
            'childposts':secondobj,
        }
        return render(req, "posts/post.html", values)

    def search_and_filter(req):
        # Получаем параметры из GET-запроса
        search_query = req.GET.get('search', '')  # Поиск по фамилии
        childpost_filter = req.GET.get('childpost', '')  # Фильтр по должности

        # Начинаем с базового запроса
        obj = PostChildModel.objects.select_related('user', 'childpost', 'post').all()

        # Фильтрация по фамилии (через связанную модель CustomUser)
        if search_query:
            obj = obj.filter(user__last_name__icontains=search_query)

        # Фильтрация по должности (NameChildPostModel)
        if childpost_filter:
            obj = obj.filter(childpost__id=childpost_filter)

        # Получаем все должности для выпадающего списка
        childposts = NameChildPostModel.objects.all()

        return render(req, 'posts/post.html', {
            'list_posts': obj,  # Передаем отфильтрованные объекты PostChildModel
            'childposts': childposts,  # Передаем все должности для формы
            'search_query': search_query,  # Передаем поисковый запрос
            'childpost_filter': childpost_filter,  # Передаем выбранную должность
        })

    def add_childpost(req):
        if req.method == 'GET':
            obj = NameChildPostModel.objects.all()
            form = NameChildPostForm()
            values = {
                'childposts':obj,
                'form':form,
            }
            return render(req, 'posts/child_post.html', values)
        if req.method == 'POST':
            form = NameChildPostForm(req.POST)
            if form.is_valid():
                form.save()  # Сохраняем новую должность в базу данных
                return redirect('admin-add-childpost')  # Перенаправляем на страницу с таблицей
        else:
            form = NameChildPostForm()  # Пустая форма для GET-запроса

        return render(req, 'add_childpost.html', {'form': form})
    

    def del_childpost(req, id):
        NameChildPostModel.objects.get(pk=id).delete()
        return redirect('admin-add-childpost')  # Перенаправляем на страницу с таблицей
    
    def del_childpost_user(req, id):
        PostChildModel.objects.get(pk=id).delete()
        return redirect('admin_post_list')  # Перенаправляем на страницу с таблицей
    
    def create_workaround(req):
        steps_db = NameChildPostModel.objects.all()
        step_templates = {
            'dismissal': list(steps_db.filter(type_for_list__name='Увольнение').values_list('name','pk')),
            'vacation': list(steps_db.filter(type_for_list__name='Отпуск').values_list('name','pk')),
            'hiring': list(steps_db.filter(type_for_list__name='Принятие на работу').values_list('name','pk')),
        }

        if req.method == 'POST':
            form = WorkaroundForm(req.POST)
            if form.is_valid():
                workaround = form.save(commit=False)
                
                # Сопоставляем коды с названиями в базе
                type_name = form.cleaned_data['typ']
      
                # Получаем объект typWorkAround
                workaround.typ = typWorkAround.objects.get(name=type_name)
                
                workaround.status = StatusModel.objects.get(name='В процессе')
                workaround.save()

                formset = SheetFormSet(req.POST, prefix='sheets', instance=workaround)
                if formset.is_valid():
                    formset.save()
                    messages.success(req, "Обходной лист успешно создан!")
                    return redirect('admin-workaround-detail', pk=workaround.pk)
                else:
                    messages.error(req, "Ошибка при создании этапов. Проверьте данные.")
            else:
                messages.error(req, "Ошибка при создании обходного листа. Проверьте данные.")
        else:
            form = WorkaroundForm()
            formset = SheetFormSet(prefix='sheets')

        return render(req, 'obhod/create.html', {
            'form': form,
            'formset': formset,
            'step_templates': step_templates
        })

   
    # def create_workaround(req):
    #     TEMPLATE_STEPS = {
    #         'увольнение': ['Отдел кадров', 'Бухгалтерия', 'Зав. отделением'],
    #         'отпуск': ['Отдел кадров', 'Руководитель'],
    #         'принятие на работу': ['Кадровик', 'Директор', 'IT отдел']
    #     }
    #     if req.method == 'POST':
    #         form = WorkaroundForm(req.POST)
    #         print(req.POST)
    #         if form.is_valid():
    #             # Сначала сохраняем WorkaroundModel
    #             workaround = form.save(commit=False)
    #             workaround.status = StatusModel.objects.get(name='В процессе')
    #             workaround.save()  # Сохраняем в базу данных

    #             # Создаем формсет с сохраненным объектом workaround
    #             formset = SheetFormSet(req.POST, prefix='sheets', instance=workaround)
                
    #             if formset.is_valid():
    #                 # Сохраняем этапы
    #                 formset.save()
                    
    #                 messages.success(req, "Обходной лист успешно создан!")
    #                 return redirect('admin-workaround-detail', pk=workaround.pk)
    #             else:
    #                 # Если формсет невалиден, добавляем ошибки
    #                 messages.error(req, "Ошибка при создании этапов. Проверьте данные.")
    #         else:
    #             # Если форма невалидна, добавляем ошибки
    #             messages.error(req, "Ошибка при создании обходного листа. Проверьте данные.")
    #     else:
    #         form = WorkaroundForm()
    #         formset = SheetFormSet(prefix='sheets')
        
    #     return render(req, 'obhod/create.html', {
    #         'form': form,
    #         'formset': formset,
    #         'step_templates': TEMPLATE_STEPS  # передаём в шаблон
    #     })

    def workaround_detail(req, pk):
        workaround = get_object_or_404(WorkaroundModel, pk=pk)
        sheets = workaround.workaroundsheetmodel_set.all().order_by('order')
        
        # Для каждого этапа проверяем, может ли текущий пользователь его подписать
        for sheet in sheets:
            sheet.can_sign = req.user.has_post(sheet.depart)
            # sheet.comments = SignatureModel.objects.get(wasm=WorkaroundSheetModel.objects.get(pk=sheet.pk))
        
        # Проверка завершения
        required_sheets = sheets.filter(is_required=True)
        all_required_signed = not required_sheets.exclude(signaturemodel__isnull=False).exists()
        
        if all_required_signed and not workaround.status.name == 'Завершен':
            workaround.status = StatusModel.objects.get(name='Завершен')
            workaround.save()
        
        return render(req, 'obhod/detail.html', {
            'workaround': workaround,
            'sheets': sheets
        })


    def assign_post(req):
        if req.method == 'POST':
            print(req.POST)
            form = AssignPostForm(req.POST)
            if form.is_valid():
                try:
                    obj = PostChildModel.objects.get(user = req.POST['user'])
                    obj.childpost = NameChildPostModel.objects.get(pk = req.POST['childpost'])
                    obj.save()
                except:
                    form.save()  # Сохраняем назначение в базу данных
                return redirect('admin-filter')  # Перенаправляем на страницу с таблицей
        else:
            form = AssignPostForm()  # Пустая форма для GET-запроса

        return render(req, 'posts/add_user_post.html', {'form': form})
   

    def edit_post(req, post_id):
        # Получаем объект PostChildModel по ID
        post_child = get_object_or_404(PostChildModel, id=post_id)

        if req.method == 'POST':
            form = EditPostForm(req.POST, instance=post_child)
            if form.is_valid():
                form.save()  # Сохраняем изменения
                return redirect('admin-filter')  # Перенаправляем на страницу с таблицей
        else:
            form = EditPostForm(instance=post_child)  # Заполняем форму текущими данными

        return render(req, 'posts/edit_user_post.html', {'form': form, 'post_child': post_child})

    
    def user_list(req):
        # Получаем параметры из GET-запроса
        search_query = req.GET.get('search', '')
        department_filter = req.GET.get('department', '')
        role_filter = req.GET.get('role', '')

        # Начинаем с базового запроса
        users = CustomUser.objects.all()

        # Фильтрация по фамилии
        if search_query:
            users = users.filter(last_name__icontains=search_query)

        # Фильтрация по отделению
        if department_filter:
            users = users.filter(depart__id=department_filter)

        # Фильтрация по роли
        if role_filter:
            users = users.filter(role__id=role_filter)

        # Форма для поиска и фильтрации
        form = UserSearchForm(req.GET)

        return render(req, 'user/list_users.html', {
            'users': users,
            'form': form,
            'search_query': search_query,
            'department_filter': department_filter,
            'role_filter': role_filter,
        })

    def edit_user(req, user_id):
        user = get_object_or_404(CustomUser, id=user_id)

        if req.method == 'POST':
            form = CustomUserForm(req.POST, instance=user)
            if form.is_valid():
                form.save()
                return redirect('user-list')  # Перенаправляем на список пользователей
        else:
            form = CustomUserForm(instance=user)

        return render(req, 'user/edit_user.html', {'form': form, 'user': user})
    
    def delete_user(req, user_id):
        WorkaroundModel.objects.filter(user__id=user_id).delete()
        get_object_or_404(CustomUser, id=user_id).delete()
        return redirect('user-list')  # Перенаправляем на список пользователей

    def department_list(req):
        departments = DepartmentModel.objects.all()
        return render(req, 'department/depart_list.html', {'departments': departments})

    def delete_department(req, department_id):
        department = get_object_or_404(DepartmentModel, id=department_id)
        department.delete()
        return redirect('admin-department-list')  # Перенаправляем на список отделений

    def add_department(req):
        if req.method == 'POST':
            name_dep = req.POST.get('name_dep')  # Получаем название отделения из формы
            if name_dep:
                DepartmentModel.objects.create(name_dep=name_dep)  # Создаем новое отделение
            return redirect('admin-department-list')  # Перенаправляем на список отделений
        return redirect('admin-department-list')  # Если метод не POST, просто перенаправляем

    def sign_sheet(req, sheet_id):
        sheet = get_object_or_404(WorkaroundSheetModel, id=sheet_id)
        if req.user.signature:
            # Проверка прав доступа
            if not req.user.has_post(sheet.depart):
                messages.error(req, "У вас нет прав для подписания этого пункта")
                messages.type = "danger"
                return redirect('admin-workaround-list')
            
            # Проверка порядка подписания
            unsigned_sheets = WorkaroundSheetModel.objects.filter(
                workaround=sheet.workaround,
                order__lt=sheet.order,
                signaturemodel__user__isnull=True,
                is_required=True
            ).exists()
            
            if unsigned_sheets:
                messages.error(
                    req, 
                    f"Необходимо сначала подписать предыдущие обязательные пункты (порядковый номер {sheet.order})"
                )
                messages.type="warning"
                return redirect('admin-workaround-detail', pk=sheet.workaround.pk)
            
            # Создание подписи
            SignatureModel.objects.create(
                wam=sheet.workaround,
                wasm=sheet,
                user=req.user,
                comment="Подписано"
            )
            
            messages.success(req, "Пункт успешно подписан")
            messages.type='success'
            return redirect('admin-workaround-detail', pk=sheet.workaround.pk)
        else:
            return redirect('sign')


    def workaround_list(req):

        user_childpost_ids = NameChildPostModel.objects.filter(
            postchildmodel__user=req.user
        ).values('id')

        
        relevant_points = WorkaroundSheetModel.objects.filter(
            workaround=OuterRef('pk'),
            depart_id__in=Subquery(user_childpost_ids)
        )

      
        workarounds = WorkaroundModel.objects.annotate(
            total_signatures=Count('signaturemodel'),
            completed_signatures=Count('signaturemodel', filter=Q(signaturemodel__user__isnull=False))
        ).select_related('user', 'typ', 'status').filter(
            Q(user__depart=req.user.depart),
            Q(Exists(relevant_points))
        )

        return render(req, 'obhod/list.html', {
            'workarounds': workarounds
        })

    
    @login_required
    def delete_workaround(req, pk):
        workaround = get_object_or_404(WorkaroundModel, pk=pk)
        
        # Проверка прав (пример - только админы или создатели могут удалять)
        if req.user.is_staff or workaround.user == req.user:
            workaround.delete()
        
        return redirect('workaround-list')


class ProfileUserView(View):
    """
    Данная функция включает в себя работу с обходными листами, создание подписи
    , смена подписи и регистрация
    """
    def logout(req):
        logout(req)
        return redirect('index')

    @login_required
    def deleteWorkaround(req, id):
        try:
            workaround = WorkaroundModel.objects.get(pk=id)
            if req.user.is_superuser or workaround.user == req.user:
                workaround.delete()
                return redirect('obhod_list_ot')
            else:
                return render(req, 'error.html', {'error': 'У вас нет прав на удаление этого обходного листа'})
        except WorkaroundModel.DoesNotExist:
            return render(req, 'error.html', {'error': 'Обходной лист не найден'})

    def user_delete(req, id):
        user = CustomUser.objects.get(pk=id)
        # Удаляем связанные записи
        PostChildModel.objects.filter(user=user).delete()
        SignatureModel.objects.filter(user=user).delete()
        WorkaroundModel.objects.filter(user=user).delete()
        # Добавьте другие модели, которые ссылаются на CustomUser
        # Удаляем пользователя
        user.delete()
        return redirect('list_user-admin')
    

    @login_required
    def myObhod(req):
        if req.method == "GET":
            obj = WorkaroundModel.objects.prefetch_related('signaturemodel_set').filter(user=req.user)
            return render(req, 'obhod/my_obhod.html', {'myl': obj})


    @login_required
    def profile(req):
        workarounds = WorkaroundModel.objects.filter(user=req.user)
        statuss=None
        try:
            statuss = PostChildModel.objects.get(user = req.user).childpost.name
        except Exception as e:
            statuss = 'нет должности'
        return render(req, 'profile.html', {'workarounds': workarounds, 'st':statuss})

    @login_required
    def sign(req):
        if req.method == "POST":
            signature_data = req.POST.get('signature_data')
            user = CustomUser.objects.get(pk=req.user.pk)
            print('я тут')
            if signature_data:
                
                save_signature_from_base64(signature_data, req.user)
                return redirect('sign')
        return render(req, 'sign.html', {'signat': req.user.signature})

    @login_required
    def sign_delete(req):
        print('я тут')
        if req.user.is_superuser or RoleModel.objects.get(name=req.user.role).name == "Ответственный":
            req.user.signature.delete()
        return redirect('sign')

    @login_required
    def take_post(req):
        if req.user.is_superuser or req.user.role == RoleModel.objects.get(name='Ответственный'):
            if req.method == "POST":
                req.user.post = PostModel.objects.get(pk=req.POST['post'])
                req.user.save()
                return redirect('profile')
            return render(req, 'post.html', {'posts': PostModel.objects.all()})
        return redirect('profile')
