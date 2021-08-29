import sys
import io
import xml.etree.ElementTree as ET
import json
import requests as rq
from config import Config

args = sys.argv
valuta = {}
cenGruppi = {}
nomenk = {}


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

    info = io.open('info.txt', mode='w', encoding='utf-8')
    info.write(json.dumps(nomenk))

    print('Parsing done!')

    allDiscs = rq.post('https://xn--e1amjcn.xn--p1ai/rest/tcatalog/getDiscounts/',
                       data={'auth': Config.authToken})
    print(allDiscs.status_code, allDiscs.reason)
    print(allDiscs.text[:300])


if __name__ == '__main__':
    main()
