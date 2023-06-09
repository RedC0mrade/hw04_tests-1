from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group, User
from posts.forms import PostForm
from yatube.settings import NUMBER_OF_POSTS_IN_PAG

TOTAL_NUMBER_OF_POSTS = 13


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='test*100'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post(self, response, is_post=False):
        if is_post:
            post = response.context['post']
        else:
            post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pub_date, self.post.pub_date)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:index'))
        self.check_post(response)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.assertIn('group', response.context)
        group = response.context.get('group')
        self.assertEqual(group, self.group)
        self.check_post(response)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', args=(self.user.username,)))
        self.assertIn('author', response.context)
        author = response.context.get('author')
        self.assertEqual(author, self.user)
        self.check_post(response)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', args=(self.post.id,)))
        self.check_post(response, is_post=True)

    def test_create_forms_value(self):
        """Проверка формы."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        urls = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        for url, slug in urls:
            reverse_name = reverse(url, args=slug)
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_post_in_wrong_group(self):
        """Проверка, что пост не попал в неправильную группу"""
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='Новое описание',
        )
        response = self.client.get(reverse('posts:group_list',
                                           args=(new_group.slug,)))
        self.assertEqual(len(response.context['page_obj']), 0)
        post = Post.objects.first()
        self.assertEqual(post.group, self.group)
        response = self.client.get(reverse('posts:group_list',
                                           args=(self.group.slug,)))
        self.assertIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create(
            [Post(author=cls.user,
                  text=f'{index}',
                  group=cls.group) for index in range(TOTAL_NUMBER_OF_POSTS)]
        )

    def test_page(self):
        reverse_names = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
        )
        posts_in_page = (
            ('?page=1', NUMBER_OF_POSTS_IN_PAG),
            ('?page=2', TOTAL_NUMBER_OF_POSTS - NUMBER_OF_POSTS_IN_PAG),
        )
        for name, args in reverse_names:
            with self.subTest(name=name):
                for page, number in posts_in_page:
                    with self.subTest(page=page):
                        response = self.client.get(reverse(name,
                                                           args=args) + page)
                        self.assertEqual(len(response.context['page_obj']),
                                         number)
