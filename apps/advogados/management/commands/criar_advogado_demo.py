from django.core.management.base import BaseCommand

from apps.advogados.models import Advogado, InscricaoOab, TipoInscricaoOab, UnidadeFederativa
from apps.contas.models import Usuario
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


class Command(BaseCommand):
    help = "Cria usuário fictício de advogado para desenvolvimento."

    def handle(self, *args, **options):
        login = "advogado"
        email = "advogado@jurisly.com"
        senha = "advogado123"

        usuario = Usuario.objects.filter(login=login).first()
        if usuario is None:
            usuario = Usuario.objects.filter(email=email).first()
        criado = usuario is None
        if criado:
            usuario = Usuario(login=login, email=email)
        usuario.login = login
        usuario.email = email
        usuario.nome = "Gabriel"
        usuario.sobrenome = "Souza"
        usuario.ativo = True
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.set_password(senha)
        usuario.save()

        org, _ = Organizacao.objects.get_or_create(
            slug="escritorio-gabriel",
            defaults={"nome": "Escritório Gabriel Souza", "ativo": True},
        )

        OrganizacaoUsuario.objects.get_or_create(
            organizacao=org,
            usuario=usuario,
            defaults={
                "perfil": PerfilOrganizacao.ADVOGADO,
                "ativo": True,
            },
        )

        advogado, adv_criado = Advogado.objects.update_or_create(
            usuario=usuario,
            defaults={
                "organizacao": org,
                "nome_completo": "Gabriel Souza",
                "nome_consulta": "",
                "email": email,
                "telefone": "11987654321",
                "cpf": "52998224725",
                "ativo": True,
            },
        )

        inscricao, _ = InscricaoOab.objects.update_or_create(
            advogado=advogado,
            numero="496901",
            uf=UnidadeFederativa.SP,
            defaults={
                "tipo": TipoInscricaoOab.PRINCIPAL,
                "principal": True,
                "ativo": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Usuário fictício pronto."))
        self.stdout.write(f"  login: {login}")
        self.stdout.write(f"  e-mail: {email}")
        self.stdout.write(f"  senha: {senha}")
        self.stdout.write(f"  oab: {inscricao.oab_formatada}")
        self.stdout.write(f"  usuario_novo={criado} perfil_novo={adv_criado}")
