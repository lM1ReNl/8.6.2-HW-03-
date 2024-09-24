from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User, Group
from django.http import request
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django_filters.views import FilterView
from django.shortcuts import render, redirect
from .forms import PostForm, ProfileForm
from .models import Post, BaseRegisterForm, Author
from .filters import PostFilter


class PostList(ListView):
    model = Post
    ordering = '-creation_date'
    template_name = 'news.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'
    pk_url_kwarg = 'id'


class PostSearch(FilterView):
    model = Post
    filterset_class = PostFilter
    template_name = 'search.html'
    context_object_name = 'news'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = PostFilter(self.request.GET, queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class PostCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'news.add_post'  # , 'articles.add_post'
    form_class = PostForm
    model = Post
    template_name = 'post_create.html'
    context_object_name = 'create'
    success_url = reverse_lazy('post_list')
    login_url = reverse_lazy('post_list')


    def form_valid(self, form):
        post = form.save(commit=False)
        if 'news' in self.request.path:
            post.type = 'NE'
        else:
            post.type = 'AR'
        post.author = self.request.user.author
        post.save()

        return super().form_valid(form)


class PostUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'news.change_post'
    form_class = PostForm
    model = Post
    template_name = 'post_edit.html'


class PostDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'news.delete_post'
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('post_list')


class BaseRegisterView(CreateView):
    model = User
    form_class = BaseRegisterForm
    success_url = '/'


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'news/index.html'
    # context_object_name = 'author_view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_authors'] = not self.request.user.groups.filter(name='authors').exists()
        return context


class ProfileUpdate(LoginRequiredMixin, UpdateView):
    template_name = 'profile_edit.html'
    form_class = ProfileForm
    model = Author
    success_url = reverse_lazy('post_list')


@login_required
def upgrade_me(request):
    user = request.user
    authors_group = Group.objects.get(name='authors')
    if not request.user.groups.filter(name='authors').exists():
        authors_group.user_set.add(user)
        Author.objects.create(user=user)
    return redirect('/profile/')  # или /news/
