import sys
import io
import os
import xml.etree.ElementTree as ET
import json
import requests as rq
import time
import datetime
from urllib.parse import quote
from config import Config

args = sys.argv
valuta = {}
cenGruppi = {}
nomenk = {}

utochneniya = []
prices = []

cenGruppi2 = {}
nomenk2 = {}
discType2 = {}


def loadUtochneniya():
    try:
        resp = rq.post(Config.url + '/rest/personal/resetUtoch/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset prices.')

    xmlUtochneniya = io.open(Config.pathToFiles + "utochneniya.xml", mode="r", encoding="utf-8")
    tmpstr = xmlUtochneniya.read()
    xmlUtochneniyaRoot = ET.fromstring(tmpstr)
    vidCeni = {}
    soglasheniya = {}
    for child in xmlUtochneniyaRoot:
        tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7 = '', '', '', '', '', '', ''
        for part in child:
            if 'ИдСоглашения' == part.tag:
                tmp1 = part.text
            if 'ИдВидЦены' == part.tag:
                tmp2 = part.text
            if 'ИдЦеноваяГруппа' == part.tag:
                tmp3 = part.text
            if 'ЗначениеПроцентРучнойСкидки' == part.tag:
                tmp4 = part.text
            if 'ЗначениеПроцентРучнойНаценки' == part.tag:
                tmp5 = part.text
            if 'НаименованиеВидЦены' == part.tag:
                tmp6 = part.text
            if 'НаименованиеСоглашения' == part.tag:
                tmp7 = part.text
        utochneniya.append(
            {'UF_SOGLASHENIE_ID': tmp1, 'UF_VID_CENI_ID': tmp2, 'UF_CEN_GRUPPA_ID': tmp3, 'UF_SKIDKA_PERCENT': tmp4,
             'UF_NACENKA_PERCENT': tmp5})
        vidCeni[tmp2] = {'UF_VID_CENI_ID': tmp2, 'UF_VID_CENI_NAME': tmp6}
        soglasheniya[tmp1] = {'UF_SOGL_ID': tmp1, 'UF_SOGL_NAME': tmp7}
    try:
        resp = rq.post(Config.url + '/rest/personal/resetSogl/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset sogl.')
    try:
        resp = rq.post(Config.url + '/rest/personal/addSogl/',
                       data={'auth': Config.authToken, 'data': json.dumps(soglasheniya)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add sogl.')
    try:
        resp = rq.post(Config.url + '/rest/personal/resetVidCeni/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset vidCeni.')
    try:
        resp = rq.post(Config.url + '/rest/personal/addVidCeni/',
                       data={'auth': Config.authToken, 'data': json.dumps(vidCeni)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add vidCeni.')
    utoch_i = 1
    page_i = 1
    utochToSend = []
    for utoch in utochneniya:
        utochToSend.append(utoch)
        if utoch_i == 1000:
            utoch_i = 0
            try:
                resp = rq.post(Config.url + '/rest/personal/addUtoch/',
                               data={'auth': Config.authToken, 'data': json.dumps(utochToSend)}).text
                print(resp, page_i)
                page_i += 1
            except rq.exceptions:
                log('error', 'Cant add utoch.')
            utochToSend = []
            time.sleep(Config.deleteTimeout)
        utoch_i += 1
    try:
        resp = rq.post(Config.url + '/rest/personal/addUtoch/',
                       data={'auth': Config.authToken, 'data': json.dumps(utochToSend)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add utoch.')


def loadPrices():
    xmlPrices = io.open(Config.pathToFiles + "prices.xml", mode="r", encoding="utf-8")
    tmpstr = xmlPrices.read()
    pricesRoot = ET.fromstring(tmpstr)
    for child in pricesRoot:
        tmp1, tmp2, tmp3, tmp4 = '', '', '', ''
        for part in child:
            if 'ИдВалюты' == part.tag:
                tmp1 = part.text
            if 'ИдВидЦены' == part.tag:
                tmp2 = part.text
            if 'ИдНоменклатура' == part.tag:
                tmp3 = part.text
            if 'ЗначениеЦены' == part.tag:
                tmp4 = part.text
        prices.append({'UF_VALUTA_ID': tmp1, 'UF_VID_CENI_ID': tmp2, 'UF_TOVAR_ID': tmp3, 'UF_PRICE': tmp4})

    try:
        resp = rq.post(Config.url + '/rest/personal/resetPrices/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset prices.')
    price_i = 1
    page_i = 1
    priceToSend = []
    for price in prices:
        priceToSend.append(price)
        if price_i == 1000:
            price_i = 0
            try:
                resp = rq.post(Config.url + '/rest/personal/addPrices/',
                               data={'auth': Config.authToken, 'data': json.dumps(priceToSend)}).text
                print(resp, page_i)
                page_i += 1
            except rq.exceptions:
                log('error', 'Cant add prices.')
            priceToSend = []
            # time.sleep(Config.deleteTimeout)
            # break
        price_i += 1
    try:
        resp = rq.post(Config.url + '/rest/personal/addPrices/',
                       data={'auth': Config.authToken, 'data': json.dumps(priceToSend)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add prices.')


def loadValuta():
    xmlCurrency = io.open(Config.pathToFiles + "currency.xml", mode="r", encoding="utf-8")
    tmpstr = xmlCurrency.read()
    currencyRoot = ET.fromstring(tmpstr)
    for child in currencyRoot:
        tmpValuta = ''
        tmpValue = ''
        tmpName = ''
        for part in child:
            if 'ИдВалюта' == part.tag:
                tmpValuta = part.text
            if 'Курс' == part.tag:
                tmpValue = part.text
            if 'Валюта' == part.tag:
                tmpName = part.text
        valuta[tmpValuta] = {'UF_VALUTA_ID': tmpValuta, 'UF_VALUTA_KURS': tmpValue, 'UF_VALUTA_NAME': tmpName}
    try:
        resp = rq.post(Config.url + '/rest/personal/resetValuta/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset valuta.')
    try:
        resp = rq.post(Config.url + '/rest/personal/addValuta/',
                       data={'auth': Config.authToken, 'data': json.dumps(valuta)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add valuta.')


def loadDiscounts2():
    discs2 = []
    cenGrToSend = {}
    users = {}
    xmlDisc = io.open(Config.pathToFiles + "discounts2.xml", mode="r", encoding="utf-8")
    tmpstr = xmlDisc.read()
    discRoot = ET.fromstring(tmpstr)
    for child in discRoot:
        tmp1, tmp2, tmp3, tmp4, tmp5, tmp6 = '', '', '', '', '', ''
        for part in child:
            if 'ИдСкидки' == part.tag:
                tmp1 = part.text
            if 'НаименованиеСкидки' == part.tag:
                tmp2 = part.text
            if 'ИдЦеноваяГруппа' == part.tag:
                tmp3 = part.text
            if 'НаименованиеЦеноваяГруппа' == part.tag:
                tmp4 = part.text
            if 'ИдНоменклатура' == part.tag:
                tmp5 = part.text
            if 'ЗначениеСкидкиНаценки' == part.tag:
                tmp6 = part.text
        users[tmp1] = {'UF_USER_ID': tmp1, 'UF_USER_NAME': tmp2}
        cenGrToSend[tmp3] = {'UF_CEN_GRUPPA_ID': tmp3, 'UF_CEN_GRUPPA_NAME': tmp4}
        discs2.append({'UF_SKIDKA_ID': tmp1, 'UF_CEN_GRUPPA_ID': tmp3, 'UF_TOVAR_ID': tmp5,
                       'UF_SKIDKA_VALUE': tmp6})
    try:
        resp = rq.post(Config.url + '/rest/personal/resetUsers/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset users.')
    try:
        resp = rq.post(Config.url + '/rest/personal/addUsers/',
                       data={'auth': Config.authToken, 'data': json.dumps(users)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add users.')
    try:
        resp = rq.post(Config.url + '/rest/personal/resetCenGruppi/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset cen gruppi.')
    try:
        resp = rq.post(Config.url + '/rest/personal/addCenGruppi/',
                       data={'auth': Config.authToken, 'data': json.dumps(cenGrToSend)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add cen gruppi.')
    try:
        resp = rq.post(Config.url + '/rest/personal/resetSkidki/',
                       data={'auth': Config.authToken}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant reset skidki.')
    discToSend = []
    disc_i = 1
    page_i = 1
    for disc2 in discs2:
        discToSend.append(disc2)
        if disc_i == 1000:
            disc_i = 0
            try:
                resp = rq.post(Config.url + '/rest/personal/addSkidki/',
                               data={'auth': Config.authToken, 'data': json.dumps(discToSend)}).text
                print(resp, page_i)
                page_i += 1
            except rq.exceptions:
                log('error', 'Cant add prices.')
            discToSend = []
            time.sleep(Config.deleteTimeout)
        disc_i += 1
    try:
        resp = rq.post(Config.url + '/rest/personal/addSkidki/',
                       data={'auth': Config.authToken, 'data': json.dumps(discToSend)}).text
        print(resp)
    except rq.exceptions:
        log('error', 'Cant add skidki.')


def main():
    loadValuta()
    loadUtochneniya()
    loadDiscounts2()
    loadPrices()

    return

    xmlDiscounts = io.open(Config.pathToFiles + "discounts.xml", mode="r", encoding="utf-8")
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

    xmlNom = io.open(Config.pathToFiles + "nom.xml", mode="r", encoding="utf-8")
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

    xmlDiscounts2 = io.open(Config.pathToFiles + "discounts2.xml", mode="r", encoding="utf-8")
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
                    cenGruppi2[tmpCGId] = {'id': tmpCGId, 'name': tmpCGName, 'products': [tmpNomId],
                                           'value': tmpDiscValue}
                    prodsTotal2 += 1
        if tmpDiscId is not None and '' != tmpDiscId:
            discType2[tmpDiscId] = {'id': tmpDiscId, 'name': tmpDiscName}

    log('upload', 'Parsed: ' + str(len(cenGruppi2)) + ' discounts + ' + str(prodsTotal2) + ' products.')
    allDiscs = rq.post(Config.url + '/rest/tcatalog/getDiscounts/',
                       data={'auth': Config.authToken})
    downDiscs = []
    if 200 == allDiscs.status_code:
        downDiscs = json.loads(allDiscs.text)
    else:
        log('error', 'Cant get discounts. Attempt 2.')
        time.sleep(300)
        allDiscs = rq.post(Config.url + '/rest/tcatalog/getDiscounts/',
                           data={'auth': Config.authToken})
        if 200 == allDiscs.status_code:
            downDiscs = json.loads(allDiscs.text)

    if downDiscs == [] or downDiscs is None:
        log('error', 'Cant get discounts. Exiting.')
        sendMess('no connection. Exit.')
        return

    ldown = io.open('ldown.txt', mode='w', encoding='utf-8')
    ldown.write(json.dumps(downDiscs))

    guidToDel = []
    guidToAdd = []

    # цикл по выгруженным с сайта скидкам (1 скидка на ценовую группу)
    if downDiscs['discounts'] > 0:
        for cgDiscGuid, cgDisc in downDiscs['data'].items():
            log('test', cgDiscGuid + ' ' + str(len(cgDisc['products'])) + ' val: ' + cgDisc['value'])
            if cgDiscGuid in cenGruppi2.keys():  # если скидка на сайте есть в выгрузке из 1с
                diff = False
                # совпадает количество товаров и размер у скидки?
                if len(cenGruppi2[cgDisc['guid']]['products']) == len(
                        cgDisc['products']) and cgDisc['value'] == cenGruppi2[cgDisc['guid']]['value']:
                    equals = 0
                    for prodId in cenGruppi2[cgDisc['guid']]['products']:  # сопоставляем айди товаров в цикле
                        if prodId in cgDisc['products']:
                            equals += 1
                            continue
                        diff = True
                else:
                    diff = True
                if diff:
                    guidToDel.append(cgDisc['id'])
                    guidToAdd.append(cgDisc['guid'])
            else:
                guidToDel.append(cgDisc['id'])  # к удалению скидки которых нет в 1с

    guidsInDownload = list(map(lambda x: downDiscs['data'][x]['guid'], downDiscs['data']))
    for cg2 in cenGruppi2:  # цикл по скидкам из 1с
        if cg2 not in guidsInDownload:
            guidToAdd.append(cg2)

    errorNumber = 0
    addNumber = 0
    deleteNumber = 0
    guidErrorDelete = []
    guidErrorAdd = []
    log('upload', 'Discs to delete:' + str(len(guidToDel)) + ', Discs to add:' + str(len(guidToAdd)))
    i = 0
    for guid in guidToDel:
        i += 1
        resp = ''
        try:
            resp = rq.post(Config.url + '/rest/tcatalog/deleteDiscount/',
                           data={'auth': Config.authToken, 'id': guid}).text
        except rq.exceptions:
            errorNumber += 1
            log('error', 'Cant delete discount: ' + guid)
        ans = {}
        try:
            ans = json.loads(resp)
        except json.JSONDecodeError:
            errorNumber += 1
            log('error', 'Error deleting discount: ' + guid + '\n\tresponse: ' + resp)
            ans['result'] = 'error'

        if resp == '' or ans == {} or ans['result'] == 'error':
            errorNumber += 1
            guidErrorDelete.append(guid)
        else:
            deleteNumber += 1
        time.sleep(Config.deleteTimeout)

    i = 0
    for guid in guidToAdd:
        i += 1
        productString = ''
        for item in cenGruppi2[guid]['products']:
            productString += item + ','
        productString = productString[:-1]
        resp = ''
        try:
            resp = rq.post(Config.url + '/rest/tcatalog/addDiscount/',
                           data={'auth': Config.authToken, 'guid': guid, 'value': cenGruppi2[guid]['value'],
                                 'name': cenGruppi2[guid]['name'], 'id': productString}).text
        except rq.exceptions:
            errorNumber += 1
            log('error', 'Cant add discount: ' + guid)

        ans = {}
        try:
            ans = json.loads(resp)
        except json.JSONDecodeError:
            errorNumber += 1
            log('error', 'Error adding discount: ' + guid + ' Value: ' + cenGruppi2[guid]['value'] + ' Name: ' +
                cenGruppi2[guid]['name'] + ' Products: ' + productString + '\n\tresponse: ' + resp)
            ans['result'] = 'error'

        if resp == '' or ans == {} or ans['result'] == 'error':
            errorNumber += 1
            guidErrorAdd.append(guid)
        else:
            addNumber += 1
        time.sleep(Config.addTimeout)

    sendMess(f'added: {addNumber} deleted: {deleteNumber} errors: {errorNumber}')
    # while True:
    #     if len(guidErrorDelete) == 0 and len(guidErrorAdd) == 0:
    #         break
    #     gD = guidErrorDelete[:]
    #     gA = guidErrorAdd[:]
    #     guidErrorDelete = []
    #     guidErrorAdd = []
    #
    #     for guid in gD:
    #         ans = json.loads(rq.post(Config.url + '/rest/tcatalog/deleteDiscount/',
    #                                  data={'auth': Config.authToken, 'id': guid}).text)
    #         if ans['result'] == 'error':
    #             guidErrorDelete.append(guid)
    #         time.sleep(Config.deleteTimeout)
    #
    #     for guid in gA:
    #         ans = json.loads(rq.post(Config.url + '/rest/tcatalog/addDiscount/',
    #                                  data={'auth': Config.authToken, 'value': guid}).text)  # TODO: доделать данные
    #         if ans['result'] == 'error':
    #             guidErrorAdd.append(guid)
    #         time.sleep(Config.addTimeout)


def log(pref, mess, new=True):
    directory = pref + 'log/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    dt = datetime.date.today().strftime('%Y_%m_%d')
    hdl = open(directory + dt + '_log.txt', 'a')
    dt = datetime.datetime.now().strftime('%H:%M:%S')
    if new:
        hdl.write(dt + ' ' + mess + '\n')
    else:
        hdl.write(mess)
    hdl.close()


def sendMess(mess):
    msg = 'https://api.telegram.org/bot' + Config.tgToken + '/sendMessage?chat_id='
    msg += Config.tgChatId + '&parse_mode=Markdown&text=' + quote('[PyUpload] ' + mess)
    rq.get(msg)


if __name__ == '__main__':
    log('upload', 'Start 1c sync.')
    main()
    log('upload', 'End sync.\n')
