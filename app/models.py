from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
# Create your models here.

class NameChildPostModel(models.Model):
    name = models.CharField("Название", max_length=50)
    type_for_list = models.ForeignKey("typWorkAround", on_delete=models.CASCADE, verbose_name='Тип обходного')

    def __str__(self):
        return f'{self.name}'
    
    class Meta:
        verbose_name = 'Должности для отделений'
        verbose_name_plural = 'Должности для отделений'



class PostChildModel(models.Model):
    post =  models.ForeignKey("DepartmentModel", on_delete=models.CASCADE, verbose_name="Отделение", null=True)
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE, verbose_name="Пользователь")
    childpost = models.ForeignKey("NameChildPostModel", on_delete=models.CASCADE, verbose_name="Должность в отделении")
    
    def __str__(self):
        return f'{self.post}'
    
    class Meta:
        verbose_name = 'Должность в отделении'
        verbose_name_plural = 'Должность в отделении'


class PostModel(models.Model):
    name = models.CharField("Название", max_length=50)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        
# отделения
class DepartmentModel(models.Model):
    name_dep = models.CharField('Название', max_length=55)

    def __str__(self):
        return f'Отделение {self.name_dep}'

    class Meta:
        verbose_name = 'Отделения'
        verbose_name_plural = 'Отделения'
    
# status
class StatusModel(models.Model):
    name = models.CharField('Название статуса', max_length=50)
    
    def __str__(self):
        return f'{self.pk} {self.name}'

    @staticmethod
    def get_stat(text):
        return StatusModel.objects.get(name=text).pk

    class Meta:
        verbose_name = 'Статус'
        verbose_name_plural = 'Статус'
    
# роли
class RoleModel(models.Model):
    name = models.CharField("Название роли",max_length=200)
    
    def __str__(self):
        return f'{self.name}'
    
    @staticmethod
    def get_rol(text):
        return RoleModel.objects.get(name=text).pk

    class Meta:
        verbose_name = 'Роль'
        verbose_name_plural = 'Роль'
       

# пользоватеь 
class CustomUser(AbstractUser):  # custom user for Users 
    gen = (('m', 'Мужской'),('j', 'Женский'))
    patronymic = models.CharField('Отчество',max_length=250,)
    gender = models.CharField('Пол', choices=gen, max_length=3, null=True)
    birthday_date = models.DateField('Дата рождения', null=True,)
    role  = models.ForeignKey(RoleModel, on_delete=models.CASCADE, null=True, verbose_name='Роль')
    depart = models.ForeignKey(DepartmentModel, on_delete=models.CASCADE, null=True, verbose_name='Отделение')
    date_end = models.DateField('Дата завершения зачисления',null=True,)
    signature = models.ImageField('Подпись пользователя',null=True, upload_to='signatures/')
    post = models.ForeignKey(PostModel, verbose_name="Должность", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.patronymic}'

    @staticmethod #получение нужного профиля
    def get_user(request):
        return CustomUser.objects.get(
                pk=request.user.id
                )
    
    def has_post(self, post):
        """Проверяет, есть ли у пользователя указанная должность."""
        return self.postchildmodel_set.filter(childpost=post).exists()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        
class typWorkAround(models.Model):
    
    name  = models.CharField("Название типа", max_length=25)

    def __str__(self):
        return f'{self.name}'

# Пункты обходного листа
class WorkaroundSheetModel(models.Model):
    workaround = models.ForeignKey("WorkaroundModel", on_delete=models.CASCADE, null=True, verbose_name='Обходной лист')  # НОВОЕ ПОЛЕ
    nameofpoint = models.CharField('Название пункта', max_length=50)
    decription = models.TextField('Описание пункта', null=True)
    depart = models.ForeignKey(NameChildPostModel, on_delete=models.CASCADE, null=True, verbose_name='Должность для подписи')
    is_required = models.BooleanField('Обязательный этап', default=True)
    date_of_create = models.TimeField('Дата создания', auto_now_add=True)
    date_of_update = models.TimeField('Дата обновления пункта', auto_now=True)
    order = models.IntegerField('Порядок подписания', default=0)

    def __str__(self):
        return f'{self.nameofpoint} {self.depart}'

    class Meta:
        verbose_name = 'Пункты обходного листа'
        unique_together = [['workaround', 'order']]  # Уникальная комбинация
        ordering = ['order']
        verbose_name_plural = 'Пункты обходного листа'

    def clean(self):
        super().clean()
        
        # Проверка уникальности порядка в рамках одного обходного листа
        if WorkaroundSheetModel.objects.filter(
            workaround=self.workaround, 
            order=self.order
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                "Пункт с таким порядковым номером уже существует в этом обходном листе"
            )
    
    def can_sign(self):
        # Получаем все предыдущие обязательные пункты
        previous_sheets = WorkaroundSheetModel.objects.filter(
            workaround=self.workaround,
            order__lt=self.order,
            is_required=True
        )
        
        # Проверяем, что все они подписаны
        for sheet in previous_sheets:
            if not sheet.signaturemodel_set.exists():
                return False
        return True


    
# Обходной лист
class WorkaroundModel(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, verbose_name='Ключ пользователя')
    status = models.ForeignKey(StatusModel, on_delete=models.CASCADE, verbose_name='Статус', default=1)
    date_of_create = models.TimeField('Дата создания', auto_now_add=True)
    date_of_update = models.TimeField('Дата обновления', auto_now=True)
    typ = models.ForeignKey("typWorkAround", models.CASCADE)
    class Meta:
        verbose_name = 'Обходной лист'
        verbose_name_plural = 'Обходной лист'

# Подписи 
class SignatureModel(models.Model):
    wam = models.ForeignKey(WorkaroundModel, on_delete=models.CASCADE, verbose_name='Обходной лист')
    wasm = models.ForeignKey(WorkaroundSheetModel, on_delete=models.CASCADE, verbose_name='Пункт обходного листа')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name='Ключ пользователя', null=True )
    comment = models.TextField('Комментарий', null=True)
    
    def __str__(self):
        return f'{self.wam} {self.wasm}'
    
    class Meta:
        verbose_name = 'Подписи'
        verbose_name_plural = 'Подписи'