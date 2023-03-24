from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.forms import PostForm
from ..models import Post, Group, User


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
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='kok9',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='test*100'
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='ttfaf'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.post = PostPagesTests.post
        self.post2 = PostPagesTests.post2
        self.group = PostPagesTests.group
        self.user = PostPagesTests.user

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': f'{self.group.slug}'
                }): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': f'{self.user.username}'
                }): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': f'{self.post.id}'
                }): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': f'{self.post.id}'
                }): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(list(response.context['page_obj']),
                         [self.post2, self.post])

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        list_groups = list(map(lambda x: x.group,
                               response.context['page_obj']))
        for group in list_groups:
            self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        list_authors = list(map(lambda x: x['author'], response.context))
        for author in list_authors:
            self.assertEqual(author, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        self.assertEqual(post.id, self.post.id)

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
                self.assertIsInstance(response.context['form'], PostForm)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get(
                            'form').fields.get(value)
                        self.assertIsInstance(form_field, expected)

    def test_correct_display_post_with_group(self):
        """Проверка правильного отображения поста с группой"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn(self.post, response.context.get('page_obj').object_list)
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIn(self.post, response.context.get('page_obj').object_list)
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        self.assertIn(self.post, response.context.get('page_obj').object_list)
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}))
        self.assertNotIn(self.post,
                         response.context.get('page_obj').object_list)


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
        cls.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='kok9',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create(
            [Post(author=cls.user, text='a', group=cls.group2),
             Post(author=cls.user, text='b'),
             Post(author=cls.user, text='a', group=cls.group),
             Post(author=cls.user, text='a'),
             Post(author=cls.user, text='a', group=cls.group),
             Post(author=cls.user, text='a', group=cls.group),
             Post(author=cls.user, text='a', group=cls.group2),
             Post(author=cls.user, text='a'),
             Post(author=cls.user, text='a', group=cls.group),
             Post(author=cls.user, text='a', group=cls.group),
             Post(author=cls.user, text='a', group=cls.group2),
             Post(author=cls.user, text='a'),
             Post(author=cls.user, text='a')]
        )

    def setUp(self):
        self.client = Client()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': '75'}))
        self.assertEqual(len(response.context['page_obj']), 5)
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'auth'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'auth'}
                                           ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
