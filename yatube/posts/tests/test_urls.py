from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user2 = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user2)
        self.reverse_names = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:post_detail', (self.post.id,)),
            ('posts:post_edit', (self.post.id,)),
            ('posts:post_create', None),
        )

    def test_for_matching_reverse_with_hardcore(self):
        '''тест проверки соответствия, что прямые - хардкод ссылки
        равны полученным по reverse(name)'''
        reverse_for_url = (
            ('posts:index', None, '/'),
            ('posts:group_list',
             (self.group.slug,),
             f'/group/{self.group.slug}/'
             ),
            ('posts:profile',
             (self.user.username,),
             f'/profile/{self.user.username}/'
             ),
            ('posts:post_detail', (self.post.id,), f'/posts/{self.post.id}/'),
            ('posts:post_edit',
             (self.post.id,),
             f'/posts/{self.post.id}/edit/'
             ),
            ('posts:post_create', None, '/create/'),
        )
        for name, args, url in reverse_for_url:
            with self.subTest(name=name):
                reverse_url = reverse(name, args=args)
                self.assertEqual(reverse_url, url)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            ('posts:index', None, 'posts/index.html'),
            ('posts:group_list', (self.group.slug,), 'posts/group_list.html'),
            ('posts:profile', (self.user.username,), 'posts/profile.html'),
            ('posts:post_detail', (self.post.id,), 'posts/post_detail.html'),
            ('posts:post_edit', (self.post.id,), 'posts/post_create.html'),
            ('posts:post_create', None, 'posts/post_create.html'),
        )
        for name, args, template in templates_url_names:
            with self.subTest(name=name):
                response = self.author.get(reverse(name, args=args))
                self.assertTemplateUsed(response, template)

    def test_url_availability_of_urls_for_author(self):
        """Тест что все урлы доступны автору"""
        for url, args in self.reverse_names:
            with self.subTest(url=url):
                response = self.author.get(reverse(url, args=args))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_availability_of_urls_for_auth_user(self):
        """Тест что все урлы, кроме edit доступны не автору,
        с edit - редирект на пост-детаил"""
        for name, args in self.reverse_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(reverse(name, args=args),
                                                      follow=True)
                if name == 'posts:post_edit':
                    self.assertRedirects(response, reverse('posts:post_detail',
                                                           args=args))
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_availability_of_urls_for_guest(self):
        """Тест что все урлы кроме edit и create доступны анониму,
        с create и edit - редирект на авторизацию"""
        redirect_url = ('posts:post_edit', 'posts:post_create')
        for name, args in self.reverse_names:
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=args),
                                           follow=True)
                if name in redirect_url:
                    first_url = reverse('users:login')
                    next_url = reverse(name, args=args)
                    self.assertRedirects(response, (
                        f'{first_url}?next={next_url}'))
                else:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Проверка недоступности несуществующей страницы"""
        response = self.client.get('/aslfdjk/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
