# Generated by Django 3.0.1 on 2020-06-30 22:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Financeiro', '0003_auto_20200615_1549'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contratos',
            options={'permissions': (('gerar_financeiro', 'Pode Gerar Financeiro'), ('comprovante_debito', 'Imprimir Comprovante de debito'), ('listagem_contratos', 'Listar Contratos'), ('parcelas_cliente', 'Exibir Parcelos do cliente'), ('renegociacao', 'Renegociar parcelas'), ('gerador_cartas', 'Gerador de cartas'), ('cancelar_contrato', 'Cancelar contrato'), ('anular_cancelamento_contrato', 'Anular cancelamento'))},
        ),
    ]