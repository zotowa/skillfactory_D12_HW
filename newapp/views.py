from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy, resolve
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView # импоритируем необходимые дженерики
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings

from .models import Post, Author, Category
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import QuerySet
from django.core.paginator import Paginator # Импортируем класс, позволяющий удобно осуществлять постраничный вывод
from .filters import PostFilter # импортируем недавно написанный фильтр
from .forms import PostForm # импортируем нашу форму

DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

class PostList(ListView):
    model = Post  # указываем модель, объекты которой мы будем выводить
    template_name = 'newapp/news.html'  # указываем имя шаблона, в котором будет лежать HTML, в нём будут все инструкции о том, как именно пользователю должны вывестись наши объекты
    context_object_name = 'news'  # это имя списка, в котором будут лежать все объекты, его надо указать, чтобы обратиться к самому списку объектов через HTML-шаблон
    #queryset = Post.objects.order_by('-dateCreation')
   # ordering = ['-dateCreation']  # сортировка по дате в порядке убывания
    paginate_by = 10

    def get_queryset(self) -> QuerySet(any):
        post_filter = PostFilter(self.request.GET, queryset=Post.objects.all())
        return post_filter.qs.order_by('-dateCreation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = timezone.localtime(timezone.now()) # добавим переменную текущей даты time_now
        context['filter'] = PostFilter(self.request.GET, queryset=self.get_queryset())  # вписываем наш фильтр в контекст
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST) # создаём новую форму, забиваем в неё данные из POST-запроса
        if form.is_valid(): # если пользователь ввёл всё правильно и нигде не накосячил, то сохраняем новый товар
            form.save()
        return super().get(request, *args, **kwargs)

class PostDetail(DetailView):
    model = Post
    template_name = 'newapp/new_detail.html'
    context_object_name = 'news'
    queryset = Post.objects.all()

class News(View):

    def get(self, request):
        news = Post.objects.order_by('-dateCreation')
        p = Paginator(news, 1)  # Создаём объект класса пагинатор, передаём ему список наших товаров и их количество для одной страницы
        news = p.get_page(
            request.GET.get('page', 1))  # Берём номер страницы из get-запроса. Если ничего не передали, будем показывать первую страницу
        # Теперь вместо всех объектов в списке товаров хранится только нужная нам страница с товарами

        data = {
            'news': news,
        }

        return render(request, 'newapp/search.html', data)

class PostCreateView(PermissionRequiredMixin, CreateView):
    template_name = 'newapp/new_create.html'
    form_class = PostForm
    context_object_name = 'news'

    def form_valid(self, form):
        author_name = form.cleaned_data['author']

        author, created = Author.objects.get_or_create(name=author_name)

        form.instance.author = author

        return super().form_valid(form)

    # дженерик для редактирования объекта
class PostUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'newapp/new_create.html'
    form_class = PostForm
    context_object_name = 'news'

        # метод get_object мы используем вместо queryset, чтобы получить информацию об объекте который мы собираемся редактировать
    def get_object(self, **kwargs):
        id = self.kwargs.get('pk')
        return Post.objects.get(pk=id)

    # дженерик для удаления
class PostDeleteView(DeleteView):
    template_name = 'newapp/new_delete.html'
    queryset = Post.objects.all()
    success_url = reverse_lazy('newapp:news')
    context_object_name = 'news'

class PostCategoryView(ListView):
    model = Post
    template_name = 'newapp/category.html'
    context_object_name = 'news'
    ordering = ['-dateCreation']  # сортировка по дате в порядке убывания
    paginate_by = 10


    def get_queryset(self):
        self.id = resolve(self.request.path_info).kwargs['pk']
        c = Category.objects.get(id=self.id)
        queryset = Post.objects.filter(category=c)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        category = Category.objects.get(id=self.id)
        subscribed = category.subscribers.filter(email=user.email)

        if not subscribed:
            context['category'] = category
        return context

@login_required
def subscribe_to_category(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    if not category.subscribers.filter(id=user.id).exists():
        category.subscribers.add(user)
        email=user.email
        html = render_to_string(
            'mail/subscribed.html',
            {
                'category': category,
                'user': user,
            },
        )
        msg = EmailMultiAlternatives(
            subject=f'{category} subcription',
            body='',
            from_email=DEFAULT_FROM_EMAIL,
            to=[email,],
        )
        msg.attach_alternative(html, 'text/html')
        try:
            msg.send()
        except Exception as e:
            print(e)
        return redirect('newapp:news')
    return redirect(request.META.get('HTTP_REFERER'))

@login_required
def unsubscribe_from_category(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    if category.subscribers.filter(id=user.id).exists():
        category.subscribers.remove(user)
    return redirect('protect:index')

def CategoryDetailView(request, pk):
   category = Category.objects.get(pk=pk)
   is_subscribed = True if len(category.subscribers.filter(id=request.user.id)) else False

   return render(request,'newapp/category.html',
                 {'category': category,
                  'is_subscribed' : is_subscribed,
                  'subscribers': category.subscribers.all()
                  })