import sys
import io
import xml.etree.ElementTree as ET
import json
import requests as rq
import time
from config import Config

args = sys.argv
valuta = {}
cenGruppi = {}
nomenk = {}

cenGruppi2 = {}
nomenk2 = {}
discType2 = {}


def main():
    xmlCurrency = io.open("new/currency.xml", mode="r", encoding="utf-8")
    tmpstr = xmlCurrency.read()
    currencyRoot = ET.fromstring(tmpstr)
    for child in currencyRoot:
        tmpValuta = ''
        tmpValue = ''
        for part in child:
            if 'ИдВалюта' == part.tag:
                tmpValuta = part.text
            if 'Курс' == part.tag:
                tmpValue = part.text
        valuta[tmpValuta] = tmpValue

    # print(valuta)
    xmlDiscounts = io.open("new/discounts.xml", mode="r", encoding="utf-8")
    tmpstr = xmlDiscounts.read()
    discountsRoot = ET.fromstring(tmpstr)
    for child in discountsRoot:
        tmpId = ''
        tmpName = ''
        tmpValue = ''
        for part in child:
            if 'ИдЦеноваяГруппа' == part.tag:
                tmpId = part.text
            if 'НаименованиеЦеноваяГруппа' == part.tag:
                tmpName = part.text
            if 'ЗначениеСкидкиНаценки' == part.tag:
                tmpValue = part.text
        cenGruppi[tmpId] = {'id': tmpId, 'name': tmpName, 'value': tmpValue}

    # print(cenGruppi)

    xmlNom = io.open("new/nom.xml", mode="r", encoding="utf-8")
    tmpstr = xmlNom.read()
    nomRoot = ET.fromstring(tmpstr)
    prodsTotal1 = 0
    for child in nomRoot:
        tmpId = ''
        tmpName = ''
        tmpCGId = ''
        for part in child:
            if 'ИдНоменклатуры' == part.tag:
                tmpId = part.text
            if 'НазваниеНоменклатуры' == part.tag:
                tmpName = part.text
            if 'ИдЦеноваяГруппа' == part.tag:
                tmpCGId = part.text
        nomenk[tmpId] = {'id': tmpId, 'name': tmpName}
        if tmpCGId is not None and '' != tmpCGId and cenGruppi.get(tmpCGId) is not None:
            nomenk[tmpId]['cgid'] = tmpCGId
            nomenk[tmpId]['value'] = cenGruppi[tmpCGId]['value']
            prodsTotal1 += 1

    info = io.open('info.txt', mode='w', encoding='utf-8')
    info.write(json.dumps(nomenk))

    print('Parsing 1 done!')

    xmlDiscounts2 = io.open("new/discounts2.xml", mode="r", encoding="utf-8")
    tmpstr = xmlDiscounts2.read()
    discounts2Root = ET.fromstring(tmpstr)
    prodsTotal2 = 0
    for child in discounts2Root:
        tmpNomId = child[4].text
        tmpNomName = child[5].text
        tmpCGId = child[2].text
        tmpCGName = child[3].text
        tmpDiscId = child[0].text
        tmpDiscName = child[1].text
        tmpDiscValue = child[6].text

        nomenk2[tmpNomId] = {'id': tmpNomId, 'name': tmpNomName}
        if '6835f929-9b76-11e6-94dd-0025909b4565' == tmpDiscId:
            nomenk2[tmpNomId]['value'] = tmpDiscValue
            if tmpCGId is not None and '' != tmpCGId:
                nomenk2[tmpNomId]['cgid'] = tmpCGId
                if tmpCGId in cenGruppi2.keys():
                    cenGruppi2[tmpCGId]['products'].append(tmpNomId)
                    prodsTotal2 += 1
                else:
                    cenGruppi2[tmpCGId] = {'id': tmpCGId, 'name': tmpCGName, 'products': [tmpNomId]}
                    prodsTotal2 += 1
        if tmpDiscId is not None and '' != tmpDiscId:
            discType2[tmpDiscId] = {'id': tmpDiscId, 'name': tmpDiscName}

    print('Parsing 2 done!')

    # print(discType2)
    print('1', len(cenGruppi), prodsTotal1)
    print('2', len(cenGruppi2), prodsTotal2)

    allDiscs = rq.post(Config.url + '/rest/tcatalog/getDiscounts/',
                       data={'auth': Config.authToken})
    downDiscs = []
    if 200 == allDiscs.status_code:
        downDiscs = json.loads(allDiscs.text)
    else:
        time.sleep(300)
        allDiscs = rq.post(Config.url + '/rest/tcatalog/getDiscounts/',
                           data={'auth': Config.authToken})
        if 200 == allDiscs.status_code:
            downDiscs = json.loads(allDiscs.text)

    if downDiscs == [] or downDiscs is None:
        return
        # TODO: telegram error message

    guidToDel = []
    guidToAdd = []

    # print(cenGruppi2)
    # print(downDiscs)

    for cgDisc in downDiscs['data']:  # цикл по выгруженным с сайта скидкам (1 скидка на ценовую группу)
        if cgDisc['guid'] in cenGruppi2.keys():  # если скидка на сайте есть в выгрузке из 1с
            diff = False
            print(len(cenGruppi2[cgDisc['guid']]['products']), '==', len(cgDisc['products']), end='')
            if len(cenGruppi2[cgDisc['guid']]['products']) == len(
                    cgDisc['products']):  # совпадает количество товаров у скидки?
                equals = 0
                for prodId in cenGruppi2[cgDisc['guid']]['products']:  # сопоставляем айди товаров в цикле
                    # print(prodId, 'in', cgDisc['products'][0])
                    if prodId in cgDisc['products']:
                        equals += 1
                        continue
                    diff = True
                print(' ! ', equals, end='')
            else:
                diff = True
            print('')
            if diff:
                guidToDel.append(cgDisc['id'])
                guidToAdd.append(cgDisc['guid'])
        else:
            guidToDel.append(cgDisc['id'])  # к удалению скидки которых не в 1с

    # for cg2 in cenGruppi2:  # цикл по скидкам из 1с
    #     for cg1 in downDiscs['data']:
    #         if cg2['id'] == cg1
    # print('delete', len(guidToDel), guidToDel)
    # print('add', len(guidToAdd), guidToAdd)


if __name__ == '__main__':
    main()
