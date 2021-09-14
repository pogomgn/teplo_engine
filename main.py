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

cenGruppi2 = {}
nomenk2 = {}
discType2 = {}


def main():
    xmlCurrency = io.open(Config.pathToFiles + "currency.xml", mode="r", encoding="utf-8")
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
        # TODO: telegram error message

    guidToDel = []
    guidToAdd = []

    # цикл по выгруженным с сайта скидкам (1 скидка на ценовую группу)
    for cgDiscGuid, cgDisc in downDiscs['data'].items():
        if cgDiscGuid in cenGruppi2.keys():  # если скидка на сайте есть в выгрузке из 1с
            diff = False
            if len(cenGruppi2[cgDisc['guid']]['products']) == len(
                    cgDisc['products']):  # совпадает количество товаров у скидки?
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
        # print(i, {'auth': Config.authToken, 'id': guid})
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
        # print(i, {'auth': Config.authToken, 'guid': guid, 'value': cenGruppi2[guid]['value'],
        #           'name': cenGruppi2[guid]['name'], 'id': len(productString)})
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
    msg += Config.tgChatId + '&parse_mode=Markdown&text=[PyUpload] ' + mess
    msg = quote(msg)
    rq.get(msg)


if __name__ == '__main__':
    log('upload', 'Start upload discounts.')
    main()
    log('upload', 'End upload discounts.\n')
