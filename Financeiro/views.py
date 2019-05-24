from datetime import datetime
from bson import ObjectId
from django.shortcuts import render, redirect
from core.models import Uteis
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

    # Movimentação
    mov = {}
    if contrato[0].id_g6 != '':
        movimentacao = Movimentacoes()
        movimentacao.set_query_id(contrato[0].id_g6)
        mov = movimentacao.execute_one()
        mov = Uteis().total_venda(mov)

    # Carregando cliente e o saldo devedor
    cliente = {}
    if contrato[0].id_g6_cliente != '':
        cursor = PessoasMongo()
        cursor.set_query_id(contrato[0].id_g6_cliente)
        cursor.add_lookup_recebimentos()
        cursor.add_match_situacao_t('Pendente')
        cursor.add_match_ativo()
        cliente = cursor.execute_all()
        if len(cliente) > 0:
            cliente = cursor.get_saldo_devedor(cliente)[0]
        else:
            return False

    emitente = None  # Criando para validação se o emitente foi carregado
    parcelamento = []  # Criando para carregar as parcelas
    total = 0
    for x in contrato[0].parcelas.all():
        # Realizando busca no banco pelas parcelas atualizadas no sistema
        pago = 0
        financeiro.set_query_id(x.id_g6)
        result = financeiro.execute_one()

        for hist in result['Historico']:
            # Carregando emitente, caso seja False
            if not emitente:
                # Emitente
                cursor = PessoasMongo()
                cursor.set_query_id(hist['EmpresaReferencia'])
                emitente = cursor.execute_all()
                if len(emitente) > 0:
                    emitente = emitente[0]

            # Verificando quais parcelas foram quitadas
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

    total_liquido = {
        'total': total,
        'extenso': Uteis().num_to_currency(total)
    }
    total = {
        'total': total + contrato[0].desconto,
        'extenso': Uteis().num_to_currency(total + contrato[0].desconto)
    }

    # Reordenando para exibição
    parcelamento.sort(key=lambda t: t['Vencimento'])

    # Formatando documentos, caso existir
    emitente['Cnpj'] = PessoasMongo().formatar_documento(emitente['Cnpj'])
    if cliente['Cnpj'] is not None:
        cliente['Documento'] = 'CNPJ: ' + PessoasMongo().formatar_documento(cliente['Cnpj'])
    elif cliente['Cpf'] is not None:
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
            cursor = PessoasMongo()
            cursor.set_query_id(x['PessoaReferencia'])
            cliente = cursor.execute_all()
            if len(cliente) > 0:
                cliente = cliente[0]

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
    cursor = PessoasMongo()
    cursor.set_query_emitente()
    emitente = cursor.execute_all()
    if len(emitente) > 0:
        emitente = emitente[0]

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
        cursor = PessoasMongo()
        cursor.set_query_client()
        cursor.set_query_ativo()
        letras = []
        for i in range(ord('A'), ord('Z') + 1):
            letras.append(chr(i))
        clientes = cursor.execute_all()
        return render(request, 'financeiro/cartas_gerador.html', {'clientes': clientes, 'letras': letras})
    elif request.method == 'POST':
        cliente = request.POST['cliente']
        letras_inicio = request.POST['letras_inicio']
        letras_fim = request.POST['letras_fim']
        inical_vencimento = request.POST['inical_vencimento']
        final_vencimento = request.POST['final_vencimento']
        cursor = PessoasMongo()
        cursor.set_query_emitente()
        emitente = cursor.execute_all()
        if len(emitente) > 0:
            emitente = emitente[0]
        data_atual = datetime.now()
        cursor = PessoasMongo()
        if cliente != '':
            cursor.set_query_id(cliente)
        if letras_inicio != '' and letras_fim != '':
            cursor.set_query_name_range_start_with(letras_inicio, letras_fim)
        cursor.set_query_client()
        cursor.set_query_ativo()
        cursor.add_lookup_recebimentos()

        if inical_vencimento != '':
            inical_vencimento = inical_vencimento.split('-')
            cursor.add_match_vencimento_maior_igual(
                datetime.date(
                    int(inical_vencimento[0]),
                    int(inical_vencimento[1]),
                    int(inical_vencimento[2])
                )
            )

        if final_vencimento != '':
            final_vencimento = final_vencimento.split('-')
            cursor.add_match_vencimento_menor_igual(
                datetime.date(
                    int(final_vencimento[0]),
                    int(final_vencimento[1]),
                    int(final_vencimento[2])
                )
            )
        else:
            cursor.add_match_vencimento_menor_que(data_atual.strftime('%Y-%m-%d'))
        cursor.add_match_situacao_t('Pendente')
        cursor.add_match_ativo()
        pessoas = cursor.execute_all()
        pessoas = cursor.get_saldo_devedor(pessoas)
        return render(request, 'financeiro/carta_impresso.html', {'pessoas': pessoas, 'emitente': emitente,
                                                                  'data_atual': data_atual})
    else:
        return redirect('movimentacoes:listagem_prevenda')
