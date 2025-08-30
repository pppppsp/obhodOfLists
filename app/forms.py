from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import *
from .models import WorkaroundModel, WorkaroundSheetModel, SignatureModel, typWorkAround
from django.forms import inlineformset_factory


class AdminRegistrationForm(UserCreationForm):
    department = forms.ModelChoiceField(
        queryset=DepartmentModel.objects.all(),
        label="Отделение",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    role = forms.ModelChoiceField(
        queryset=RoleModel.objects.none(),  # Пустой queryset, заполним через JS
        label="Роль",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    childpost = forms.ModelChoiceField(
        queryset=NameChildPostModel.objects.all(),
        label="Должность",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ['department', 'role', 'childpost', 'first_name', 'last_name', 'patronymic', 
                  'username', 'email', 'birthday_date', 'password1', 'password2']
        widgets = {
            'birthday_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Имя', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Фамилия', 'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'placeholder': 'Отчество', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'type': 'email', 'placeholder': 'Почта', 'class': 'form-control'}),
            'username': forms.TextInput(attrs={'placeholder': 'Логин', 'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'type': 'password', 'placeholder': 'Введите пароль', 'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'type': 'password', 'placeholder': 'Повторите пароль', 'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = RoleModel.objects.all()


    
    
class SignatureForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['signature']
        

class WorkaroundSheetModelForm(forms.ModelForm):
    class Meta:
        model = WorkaroundSheetModel
        fields = ['nameofpoint', 'decription', 'depart']


class NameChildPostForm(forms.ModelForm):
    class Meta:
        model = NameChildPostModel
        fields = ['name', 'type_for_list']  # Поле для названия должности
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название должности'}),
            'type_for_list': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Введите название должности'}),
        }


class EditPostForm(forms.ModelForm):
    class Meta:
        model = PostChildModel
        fields = ['user', 'childpost']  # Поля для редактирования
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'childpost': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Опционально: можно добавить фильтрацию для выпадающих списков
        self.fields['user'].queryset = CustomUser.objects.all()
        self.fields['childpost'].queryset = NameChildPostModel.objects.all()


class AssignPostForm(forms.ModelForm):
    class Meta:
        model = PostChildModel
        fields = ['user', 'post', 'childpost']  # Поля для выбора пользователя, отделения и должности
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'post': forms.Select(attrs={'class': 'form-control'}),
            'childpost': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Опционально: можно добавить фильтрацию для выпадающих списков
        self.fields['user'].queryset = CustomUser.objects.all()
        self.fields['post'].queryset = DepartmentModel.objects.all()
        self.fields['childpost'].queryset = NameChildPostModel.objects.all()


class UserSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Фамилия'})
    )
    department = forms.ModelChoiceField(
        queryset=DepartmentModel.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    role = forms.ModelChoiceField(
        queryset=RoleModel.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'patronymic', 'depart', 'role']  # Поля для редактирования
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'patronymic': forms.TextInput(attrs={'class': 'form-control'}),
            'depart': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = DepartmentModel
        fields = ['name_dep']
        widgets = {
            'name_dep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название отделения'}),
        }


class WorkaroundForm(forms.ModelForm):
    TYPE_CHOICES = [
        ('dismissal', 'Увольнение'),
        ('vacation', 'Отпуск'),
        ('hiring', 'Принятие на работу'),
    ]

    typ = forms.ChoiceField(choices=TYPE_CHOICES, label='Тип заявления')

    class Meta:
        model = WorkaroundModel
        fields = ['user', 'typ']

    def clean_typ(self):
        value = self.cleaned_data['typ']
        name_map = {
            'dismissal': 'Увольнение',
            'vacation': 'Отпуск',
            'hiring': 'Принятие на работу',
        }

        name = name_map.get(value)
        try:
            return typWorkAround.objects.get(name=name)
        except typWorkAround.DoesNotExist:
            raise forms.ValidationError("Неверный тип обходного листа")

class SheetForm(forms.ModelForm):
    class Meta:
        model = WorkaroundSheetModel
        fields = ['nameofpoint', 'depart', 'is_required', 'order']
        widgets = {
            'depart': forms.Select(attrs={'class': 'form-select', 'id':'id_select'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

SheetFormSet = inlineformset_factory(
    WorkaroundModel,
    WorkaroundSheetModel,
    fields=('nameofpoint', 'depart', 'is_required', 'order'),
    extra=1,
    widgets={
        'nameofpoint': forms.TextInput(attrs={'class': 'form-control'}),
        'order': forms.NumberInput(attrs={'value': "1"}),
        'depart': forms.Select(attrs={'class': 'form-select'}),
        'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)
