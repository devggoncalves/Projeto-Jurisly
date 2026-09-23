from django.core.management.base import BaseCommand

from apps.contas.models import Usuario


class Command(BaseCommand):
    help = "Cria (ou atualiza) o superusuário admin do sistema."

    def handle(self, *args, **options):
        login = "admin"
        email = "admin@jurisly.com"
        senha = "SenhaForte123!"

        usuario = Usuario.objects.filter(login=login).first()
        if usuario is None:
            usuario = Usuario.objects.filter(email=email).first()
        criado = usuario is None
        if criado:
            usuario = Usuario(login=login, email=email)

        usuario.login = login
        usuario.email = email
        usuario.nome = "Admin"
        usuario.sobrenome = "Jurisly"
        usuario.ativo = True
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.deve_alterar_senha = False
        usuario.set_password(senha)
        usuario.save()

        self.stdout.write(self.style.SUCCESS("Admin do sistema pronto."))
        self.stdout.write(f"  login: {login}")
        self.stdout.write(f"  e-mail: {email}")
        self.stdout.write(f"  senha: {senha}")
        self.stdout.write(f"  novo={criado}")
