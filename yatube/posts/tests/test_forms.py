from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


class PostCreateFormTests(TestCase):
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
            text='Какой-то текст',
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        group = self.group
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 1)
        form_data = {
            'text': 'Тестовый текст',
            'group': group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               args=(self.user.username,)))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.get(
            text='Тестовый текст',
            group=group.id,
        )
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, group)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertNotEqual(post.id, self.post.id)
        self.assertTrue(Post.objects.filter(
            text='Тестовый текст',
            group=group.id,
        ).exists())

    def test_edit_post(self):
        """Редактированный пост сохраняется в БД c post_id."""
        group2 = Group.objects.create(
            title='Новая группа',
            slug='new-group',
            description='описание' * 5,
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'asdfsafd',
            'group': group2.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    args=(self.post.id,)),
        )
        post = Post.objects.get(
            text='asdfsafd',
            group=group2.id,
        )
        response = self.client.get(reverse('posts:group_list',
                                           args=(self.group.slug,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='asdfsafd',
                author=self.user,
            ).exists()
        )
