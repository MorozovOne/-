import re
import datetime
import xlsxwriter
import aiohttp
import asyncio
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
# -- библиатекииии

ua = UserAgent() # Обьявляем юзер агент

main_url = input('Откройте сайта ЕИСа, зайдите в реестр контрактов '
                 '44-ФЗ, впишите все что захотите в поиск и вставьте '
                 'url страницы сюда' + '\n')


#main_url = 'https://zakupki.gov.ru/epz/contract/search/results.html?morphology=on&fz44=on&contractStageList_0=on&contractStageList_1=on&contractStageList_2=on&contractStageList_3=on&contractStageList=0%2C1%2C2%2C3&selectedContractDataChanges=ANY&contractCurrencyID=-1&budgetLevelsIdNameHidden=%7B%7D&customerIdOrg=171941%3A%D0%90%D0%94%D0%9C%D0%98%D0%9D%D0%98%D0%A1%D0%A2%D0%A0%D0%90%D0%A6%D0%98%D0%AF+%D0%93%D0%9B%D0%90%D0%92%D0%AB+%D0%98+%D0%9F%D0%A0%D0%90%D0%92%D0%98%D0%A2%D0%95%D0%9B%D0%AC%D0%A1%D0%A2%D0%92%D0%90+%D0%A0%D0%95%D0%A1%D0%9F%D0%A3%D0%91%D0%9B%D0%98%D0%9A%D0%98+%D0%94%D0%90%D0%93%D0%95%D0%A1%D0%A2%D0%90%D0%9DzZ03032000299zZ750031zZzZ0541019009zZ&countryRegIdNameHidden=%7B%7D&sortBy=UPDATE_DATE&pageNumber=1&sortDirection=false&recordsPerPage=_10&showLotsInfoHidden=false'


headers = {'User-Agent': ua.random} # Спецом делаем рандом юзер агент чтобы ЕИС нас не заблочил к хуям
data = [
    ['URL КОНТРАКТА',
     'НОМЕР КОНТРАКТА',
     'ОБЬЕКТ ЗАКУПКИ',
     'ДАТА ЗАКЛЮЧЕНИЯ КОНТРАКТА',
     'ЦЕНА КОНТРАКТА',
     'СТОИМОСТЬ ИСПОЛНЕННЫХ ПОСТАВЩИКОМ ОБЯЗАТЕЛЬСТВ, ₽',
     'ФАКТИЧЕСКИ ОПЛАЧЕНО']
] # Создаем массив епта


async def main(): #Создаем асинхронную функцию чтобы наши вызовы не блокировались ебанным ЕИСом
    async with aiohttp.ClientSession() as session:
        async with session.get(main_url, headers=headers) as response:
            r = await aiohttp.StreamReader.read(response.content)
            soup = bs(r, 'html.parser')
            main_get_content = soup.find_all('div', class_='registry-entry__header-mid__number')
            for i in main_get_content:
                get_href = i.find('a')
                # вытаскиваем ссылки с карточек
                link_ = get_href.get('href')
                # вот эта вверхняя строчка важная хуйня что пиздец

                async with session.get('https://zakupki.gov.ru' + link_, headers=headers) as response_:
                # пишем новую with as менеджер для того чтобы вытаскивала данные с внутренней страницы карточки

                    rd = await aiohttp.StreamReader.read(response_.content)
                    # я не до конца уверен что нужен новый await но пусть будет я с асинхронным программированием не работал

                    main_soup = bs(rd, 'html.parser')
                    # общие данные

                    contract = main_soup.find('span', class_='cardMainInfo__content'
                                              ).find_next('span', class_='cardMainInfo__content').text.strip()

                    obj_contract = main_soup.find('span', class_='text-break d-block'
                                                  ).text.strip()

                    data_contract = main_soup.find('div', class_='date mt-auto'
                                                   ).find('div', class_='cardMainInfo__section'
                                                   ).find('span', class_='cardMainInfo__content').text.strip()

                    # выше вытаскиваем нужные данные (номер контракта, обьект закупки и дата заключения контракта хуль нет то

                    for get_a_href in main_soup.find_all('a', href=True, class_='tabsNav__item'):

                        async with session.get('https://zakupki.gov.ru/'+get_a_href['href'], headers=headers) as response_t:
                            read = await aiohttp.StreamReader.read(response_t.content)
                            soup_ = bs(read, 'html.parser')
                            # Снова создаем новую ассинхроную (Я НЕ ЕБУ ОНО НАДО ИЛИ НЕТ просто как иначе сканировать страницу хуй его)

                            # И создаем try except чтобы не вылетали ошибки None
                            try:
                                price_contract = soup_.find('div', class_='mb-5 pb-3'
                                                            ).find('div', class_='row blockInfo'
                                                            ).find('span', class_='section__info')
                                # цена контракта

                                price_producer = price_contract.find_next('span', class_='section__info')
                                # стоимость исполненных поставщиком обязательств

                                price_actually = price_producer.find_next('span', class_='section__info').find('span')
                                # фактически оплачено


                                main_link = 'https://zakupki.gov.ru' + link_
                                # складываем ссылки шоби короче выгрузить в эксель


                                pattern = re.compile("([\n])|([\ ]{2,})")
                                contract = re.sub(pattern, '' ,str(contract))
                                # Убираем лишние пробелы из номера контракта

                                data.append(
                                    [main_link,
                                     contract,
                                     obj_contract,
                                     data_contract,
                                     price_contract.text.strip(),
                                     price_producer.text.strip(),
                                     price_actually.text.strip()
                                     ]
                                )
                                # ДАБАвляем в массив нашЫ данные
                                print('passed')

                            except AttributeError:
                                pass # На эрорки похуй


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
# Обьявляем нашу деф асинку


with xlsxwriter.Workbook('ПарсерЕИС_гос_закупки'+ str(datetime.date.today()) +'.xlsx') as workbook:
    worksheet = workbook.add_worksheet()
    worksheet.set_column(0, 8, 35)
    row = 0
    col = 0
    for module in data:
            worksheet.write_row(row, col, module)
            row += 1
# Создаем манагер виф ЭСС чтобы добавить наш массив данных в эксель табличку


