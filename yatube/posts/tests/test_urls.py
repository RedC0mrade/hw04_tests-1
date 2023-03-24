from django.test import Client, TestCase

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='75',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_urls_exitst_at_desired_location(self):
        """Проверка доступности общедостуных адресов posts"""
        user = PostURLTests.user
        post = PostURLTests.post
        group = PostURLTests.group
        url_names = (
            '/',
            f'/group/{group.slug}/',
            f'/profile/{user.username}/',
            f'/posts/{post.id}/',
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_post_detail_url_exists_at_desired_location_authorized(self):
        """Проверка доступа к определенным страницам авторизованному
        пользователю."""
        url_names = (
            f'/posts/{PostURLTests.post.id}/edit/',
            '/create/',
        )
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_unexisting_page(self):
        """Проверка недоступности несуществующей страницы"""
        response = self.guest_client.get('/aslfdjk/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        user = PostURLTests.user
        post = PostURLTests.post
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/75/': 'posts/group_list.html',
            f'/profile/{user.username}/': 'posts/profile.html',
            f'/posts/{post.id}/': 'posts/post_detail.html',
            f'/posts/{post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
