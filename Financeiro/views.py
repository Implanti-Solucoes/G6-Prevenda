from datetime import datetime
from bson import ObjectId
from django.shortcuts import render, redirect
from core.models import Uteis, Configuracoes
from Movimentacoes.models import Movimentacoes
from .models import Financeiro, Contratos, Parcelas
from Pessoas.models import PessoasMongo


def gerar_financeiro(request):
    # Recebendo valores e tratando
    id = request.POST['id']
    conta = request.POST['conta']
    centro_custo = request.POST['centro_custo']
    planos_contas = request.POST['planos_contas']

    # Recebendo valores de entrada e tratando
    entrada = request.POST['entrada']
    entrada = float(entrada.replace(',', '.'))

    # Recebendo valores e tratando
    parcelas = int(request.POST['parcelas'])

    # Recebendo datas de vecimento
    vencimentos = request.POST.getlist('vencimentos[]')

    # Fazendo busca das prevendas
    movimentacao = Movimentacoes()
    movimentacao.set_query_id(id)
    movimentacao.set_query_t('PreVenda')
    movimentacao.set_query_convertida(False)
    cursor = movimentacao.execute_one()

    # Verificando a venda e os dados informados
    if cursor is None:
        print("Não achei a pre venda")
        return redirect('movimentacoes:listagem_prevenda')

    if 'InformacoesPesquisa' not in cursor:
        print("Achei mais não ta valida")
        return redirect('movimentacoes:listagem_prevenda')

    if cursor['Situacao']['Codigo'] != 1:
        print("Achei ta valida, mas a situação não ta boa")
        return redirect('movimentacoes:listagem_prevenda')

    if len(vencimentos) != parcelas:
        print("Tudo certo, mas os vencimentos não")
        return redirect('movimentacoes:listagem_prevenda')

    # Pegando total da nota com descontos
    cursor = Uteis().total_venda(cursor)
    cursor['liquido'] = cursor['liquido'] - entrada

    # Criado contrato
    contrato = Contratos.objects.create(
        tipo=1,
        id_g6=cursor['id'],
        id_g6_cliente=str(cursor['Pessoa']['PessoaReferencia']),
        excluido=False
    )

    # Tratando valores da parcela
    valor_parcela = 0
    if cursor['liquido'] > 0:
        valor_parcela = cursor['liquido'] / parcelas
        valor_parcela = float('%.2f' % valor_parcela)

    # gerando parcela de entrada
    if entrada > 0:
        y = 1
        id = Financeiro().gerar_parcela(
            titulo='Pre Venda',
            informacoes_pesquisa=cursor['InformacoesPesquisa'],
            pessoa=cursor['Pessoa']['PessoaReferencia'],
            emitente=cursor['Empresa']['PessoaReferencia'],
            documento=contrato.id,
            num=y,
            conta=conta,
            centro_custo=centro_custo,
            planos_contas=planos_contas,
            valor_parcela=entrada,
            vencimento=datetime.now(),
            entrada=True
        )
        if id is not None:
            contrato.parcelas.create(id_g6=id, valor=entrada)
    else:
        y = 0

    # Verificando se o total - entra / parcelas, gerou algum valor
    if valor_parcela > 0:
        for x in vencimentos:
            id = Financeiro().gerar_parcela(
                titulo='Pre Venda',
                informacoes_pesquisa=cursor['InformacoesPesquisa'],
                pessoa=cursor['Pessoa']['PessoaReferencia'],
                emitente=cursor['Empresa']['PessoaReferencia'],
                documento=contrato.id,
                num=y + 1,
                conta=conta,
                centro_custo=centro_custo,
                planos_contas=planos_contas,
                valor_parcela=valor_parcela,
                vencimento=x,
                entrada=False
            )
            if id is not None:
                contrato.parcelas.create(id_g6=id, valor=valor_parcela)
            y += 1

    # Vamos configurar as movimentações
    try:
        cursor['InformacoesPesquisa'] = Financeiro().remove_repetidos(cursor['InformacoesPesquisa'])
        # Configurando CFOP para não gerar financeiro
        z = 0
        for _ in cursor['ItensBase']:
            cursor['ItensBase'][z]['OperacaoFiscal']['Tipo'] = 5
            z = z + 1

        # Removendo totais para pode atualizar no banco
        cursor = Uteis().remover_totais(cursor)

        # Removendo ID tratado para pode inserir no banco
        del cursor['id']

        # Modificar para status aprovado
        cursor['Situacao'] = {
            '_t': [
                'SituacaoMovimentacao',
                'Aprovado'
            ],
            'Codigo': 8,
            'Descricao': 'Aprovado',
            'Cor': '#006400',
            'DescricaoComando': 'Tornar pendente'
        }

        # Modificando o número da pre-venda para o numero do contrato
        cursor['Numero'] = contrato.id

        # Atualizando movimentação
        database = Uteis().conexao
        database['Movimentacoes'].update({'_id': cursor['_id']}, cursor)
        Uteis().fecha_conexao()

        # Redirecionando para o Comprovante de debito
        return redirect('financeiro:comprovante_de_debito_por_movimentacao', contrato.id)
    except Exception as e:
        print(e)


def comprovante_de_debito_por_movimentacao(request, id):
    template_name = 'movimentacoes/comprovante_de_debito.html'

    # Estanciando classes
    financeiro = Financeiro()

    # Carregando contrato
    contrato = Contratos.objects.all().filter(id=id)

    # Cliente e Emitente
    emitente = None
    cliente = []
    mov = {}
    if contrato[0].id_g6 != '':
        movimentacao = Movimentacoes()
        movimentacao.set_query_id(contrato[0].id_g6)
        mov = movimentacao.execute_one()
        mov = Uteis().total_venda(mov)

    if contrato[0].id_g6_cliente != '':
        cliente = PessoasMongo().get_pessoa(contrato[0].id_g6_cliente)

    parcelamento = []
    total = 0
    for x in contrato[0].parcelas.all():
        # Realizando busca no banco pelas parcelas atualizadas no sistema
        pago = 0
        financeiro.set_query_id(x.id_g6)
        result = financeiro.execute_one()
        if not cliente:
            cliente = PessoasMongo().get_pessoa(result['PessoaReferencia'])
        cliente['SaldoDevedor'] = PessoasMongo().get_saldo_devedor(cliente['_id'])
        cliente['SaldoDevedor'] = (
            cliente['SaldoDevedor']['total_devedor'] +
            cliente['SaldoDevedor']['juro'] +
            cliente['SaldoDevedor']['multa']
        )

        # Verificando quais parcelas foram quitadas
        for hist in result['Historico']:
            if not emitente:
                emitente = PessoasMongo().get_pessoa(hist['EmpresaReferencia'])

            if 'HistoricoQuitado' in hist['_t'] or 'HistoricoQuitadoParcial' in hist['_t']:
                pago = hist['Valor']

        # Inserindo a informação de qual valor foi quitado ou Não
        parcelamento.append(
            {
                'Vencimento': result['Vencimento'],
                'Valor': result['Historico'][0]['Valor'],
                'Pago': pago,
                'Ativo': 'Sim' if result['Ativo'] else 'Não'
            }
        )
        total = total + result['Historico'][0]['Valor']

    total_liquido = total
    total = total + contrato[0].desconto

    # Reordenando para exibição
    parcelamento.sort(key=lambda t: t['Vencimento'])

    # Formatando documentos, caso existir
    emitente['Cnpj'] = PessoasMongo().formatar_documento(emitente['Cnpj'])
    if 'Cnpj' in cliente:
        cliente['Documento'] = 'CNPJ: ' + PessoasMongo().formatar_documento(cliente['Cnpj'])
    elif 'Cpf' in cliente:
        cliente['Documento'] = 'CPF: ' + PessoasMongo().formatar_documento(cliente['Cpf'])
    else:
        cliente['Documento'] = ''
    # Criando a variavel context para passa dados para template
    context = {
        'Mov': mov,
        'Contrato': contrato,
        'Data': datetime.now(),
        'Parcelamento': parcelamento,
        'Emitente': emitente,
        'Cliente': cliente,
        'total': total,
        'total_liquido': total_liquido
    }
    return render(request, template_name, context)


def listagem_contratos(request, id, cancelado):
    template_name = 'contratos/index.html'
    contratos_ativos = Contratos.objects.all().filter(id_g6_cliente=id, excluido=0)
    contratos_excluidos = Contratos.objects.all().filter(id_g6_cliente=id, excluido=1)

    context = {
        'contratos_ativos': contratos_ativos,
        'contratos_excluidos': contratos_excluidos,
        'cancelado': cancelado
    }
    return render(request, template_name, context)


def listagem_parcelas_cliente(request, id):
    template_name = 'financeiro/index.html'
    financeiro = Financeiro()
    financeiro.set_query_pessoa_referencia(id)
    financeiro.set_query_situacao_codigo(1)
    financeiro.set_query_ativo(True)
    parcelas_mongo = financeiro.execute_all()

    par = []
    for parcela_mongo in parcelas_mongo:
        if 'Juro' in parcela_mongo:
            parcela_mongo['Juro']['Valor'] = financeiro.calcular_juros(
                valor=parcela_mongo['Historico'][0]['Valor'],
                vencimento=parcela_mongo['Vencimento'],
                tipo=parcela_mongo['Juro']['Codigo'],
                percentual=parcela_mongo['Juro']['Percentual'],
                dias_carencia=parcela_mongo['Juro']['DiasCarencia']
            )
        else:
            parcela_mongo['Juro'] = {}
            parcela_mongo['Juro']['Valor'] = 0

        parcela = Parcelas.objects.all().filter(id_g6=str(parcela_mongo['_id']))

        if len(parcela) > 0:
            par.append(
                {
                    'parcela_mongo': parcela_mongo,
                    'contrato': parcela[0].contrato,
                }
            )
        else:
            par.append(
                {
                    'parcela_mongo': parcela_mongo
                }
            )

    return render(request, template_name, {'parcelas': par})


def renegociacao(request):
    template_name = 'financeiro/renegociar.html'
    parcelas = request.POST.getlist('parcela')
    financeiro = Financeiro()
    contas = Financeiro().get_contas
    centros_custos = Financeiro().get_centros_custos
    planos_conta = Financeiro().get_planos_conta
    cliente = None
    total = 0
    juro = 0
    multa = 0

    for parcela in parcelas:
        financeiro.set_query_id(parcela)
        financeiro.set_query_ativo(True)
        financeiro.set_query_situacao_codigo(1)
        x = financeiro.execute_one()
        if cliente is None:
            cliente = PessoasMongo().get_pessoa(x['PessoaReferencia'])
            cliente['id'] = str(cliente['_id'])

        if cliente['_id'] == x['PessoaReferencia']:
            total += x['Historico'][0]['Valor']
            if 'Juro' in x:
                juro += financeiro.calcular_juros(
                    valor=x['Historico'][0]['Valor'],
                    vencimento=x['Vencimento'],
                    tipo=x['Juro']['Codigo'],
                    percentual=x['Juro']['Percentual'],
                    dias_carencia=x['Juro']['DiasCarencia']
                )
            elif 'Multa' in x:
                multa += financeiro.calcular_juros(
                    valor=x['Historico'][0]['Valor'],
                    vencimento=x['Vencimento'],
                    tipo=3,
                    percentual=x['Multa']['Percentual'],
                    dias_carencia=x['Multa']['DiasCarencia']
                )
        financeiro.unset_all()

    valores = {
        1: total,
        2: (total+juro),
        3: (total+multa),
        4: (total+multa+juro),
    }
    context = {
        'cliente': cliente,
        'contas': contas,
        'centros_custos': centros_custos,
        'planos_conta': planos_conta,
        'valores': valores,
        'parcelas': parcelas
    }
    return render(request, template_name, context)


def renegociacao_lancamento(request):
    # Separação de dados
    conta = request.POST['conta']
    centro_custo = request.POST['centro_custo']
    planos_contas = request.POST['planos_contas']

    # Recebendo valores de entrada, desconto e tratando
    entrada = request.POST['entrada']
    entrada = float(entrada.replace(',', '.'))

    desconto = request.POST['desconto']
    desconto = float(desconto.replace(',', '.'))

    # Recebendo valores e tratando
    parcelas = request.POST.getlist('parcela')
    qant_parcelas = int(request.POST['parcelas'])

    # Dados extras
    id_cliente = request.POST['id_cliente']
    id_total = int(request.POST['total'])
    emitente = PessoasMongo().get_emitente()

    # Recebendo datas de vecimento
    vencimentos = request.POST.getlist('vencimentos[]')

    if qant_parcelas != len(vencimentos):
        print("Parcelas e vencimentos invalidos")
        return redirect('movimentacoes:listagem_prevenda')

    total = 0
    juro = 0
    multa = 0

    for parcela in parcelas:
        financeiro = Financeiro()
        financeiro.set_query_id(parcela)
        financeiro.set_query_ativo(True)
        financeiro.set_query_situacao_codigo(1)
        x = financeiro.execute_one()
        financeiro.unset_all()

        if id_cliente == str(x['PessoaReferencia']):
            # Atualizando a parcela
            database = Uteis().conexao
            database['Recebimentos'].update(
                {'_id': ObjectId(parcela)},
                {'$set': {'Ativo': False}}
            )
            Uteis().fecha_conexao()

            total += x['Historico'][0]['Valor']
            if 'Juro' in x:
                juro += financeiro.calcular_juros(
                    valor=x['Historico'][0]['Valor'],
                    vencimento=x['Vencimento'],
                    tipo=x['Juro']['Codigo'],
                    percentual=x['Juro']['Percentual'],
                    dias_carencia=x['Juro']['DiasCarencia']
                )
            elif 'Multa' in x:
                multa += financeiro.calcular_juros(
                    valor=x['Historico'][0]['Valor'],
                    vencimento=x['Vencimento'],
                    tipo=3,
                    percentual=x['Multa']['Percentual'],
                    dias_carencia=x['Multa']['DiasCarencia']
                )
        else:
            print("Parcela " + parcela + " não é do mesmo cliente")

    if id_total == 1:
        total = total - desconto
    elif id_total == 2:
        total = total + juro - entrada - desconto
    elif id_total == 3:
        total = total + multa - entrada - desconto
    elif id_total == 4:
        total = total + multa + juro - entrada - desconto
    else:
        print("Total ID é invalido")
        return redirect('movimentacoes:listagem_prevenda')

    if total <= 0:
        print("Total menor que 0 e é invalido")
        return redirect('movimentacoes:listagem_prevenda')

    # Criado contrato
    contrato = Contratos.objects.create(
        tipo=2,
        id_g6='',
        id_g6_cliente=id_cliente,
        excluido=False,
        desconto=desconto
    )

    y = 0

    if entrada > 0:
        y = 1
        id = Financeiro().gerar_parcela(
            titulo='Renegociação',
            informacoes_pesquisa=[],
            pessoa=id_cliente,
            emitente=emitente['_id'],
            documento=contrato.id,
            num=y,
            conta=conta,
            centro_custo=centro_custo,
            planos_contas=planos_contas,
            valor_parcela=entrada,
            vencimento=datetime.now(),
            entrada=True
        )
        if id is not None:
            contrato.parcelas.create(id_g6=id, valor=entrada)

    valor_parcela = total / qant_parcelas
    for x in vencimentos:
        id = Financeiro().gerar_parcela(
            titulo='Renegociação',
            informacoes_pesquisa=[],
            pessoa=id_cliente,
            emitente=emitente['_id'],
            documento=contrato.id,
            num=y+1,
            conta=conta,
            centro_custo=centro_custo,
            planos_contas=planos_contas,
            valor_parcela=valor_parcela,
            vencimento=x,
            entrada=False
        )
        if id is not None:
            contrato.parcelas.create(id_g6=id, valor=valor_parcela)
        y += 1
    return redirect('financeiro:comprovante_de_debito_por_movimentacao', contrato.id)


def cartas_gerador(request):
    if request.method == 'GET':
        clientes = Movimentacoes().get_clientes()
        return render(request, 'financeiro/cartas_gerador.html', {'clientes': clientes})
    elif request.method == 'POST':
        cliente = request.POST['cliente']
        emitente = PessoasMongo().get_emitente()
        data_atual = datetime.now()
        if cliente == '':
            pessoas = PessoasMongo().get_clientes(atrasados=True)
        else:
            pessoas = [PessoasMongo().get_pessoa(id=cliente, atrasados=True)]
        return render(request, 'financeiro/carta_impresso.html', {'pessoas': pessoas, 'emitente': emitente,
                                                                  'data_atual': data_atual})
    else:
        return redirect('movimentacoes:listagem_prevenda')
